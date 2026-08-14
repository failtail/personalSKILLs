#!/usr/bin/env node
/**
 * 从 JavaScript、TypeScript 与 Vue SFC 中生成 Project ThingJS Usage Surface。
 *
 * AST 是唯一可生成 Usage Entity 的通道；Regex 仅记录 parse failure 或当前
 * resolver 尚未覆盖的发现项，不能提升为已验证 API 使用。
 */

import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { createRequire } from 'node:module'

const SOURCE_EXTENSIONS = new Set(['.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx', '.vue'])
const SKIP_DIRECTORIES = new Set([
  '.agents',
  '.codex',
  '.codex-ref',
  '.codex-ref-repos',
  '.git',
  '.github',
  '.idea',
  '.vscode',
  'coverage',
  'dist',
  'node_modules',
])
const RESOLUTION_STATES = new Set([
  'resolved',
  'resolved_inherited',
  'ambiguous',
  'dynamic_unresolved',
  'parse_failed',
])
const THING_TOKEN_PATTERN = /\bTHING(?:\.[A-Za-z_$][\w$]*)+/g

function parseArgs(argv) {
  const values = { entries: [] }
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]
    if (arg === '--project-root') values.projectRoot = argv[++index]
    else if (arg === '--output') values.output = argv[++index]
    else if (arg === '--entry') values.entries.push(argv[++index])
    else if (arg === '--parser-root') values.parserRoot = argv[++index]
    else if (arg === '--contract') values.contract = argv[++index]
    else if (arg === '--alias-config') values.aliasConfig = argv[++index]
    else if (arg === '--changed-files') values.changedFiles = argv[++index]
    else if (arg === '--cache') values.cache = argv[++index]
    else if (arg === '--help') values.help = true
    else throw new Error(`Unknown argument: ${arg}`)
  }
  return values
}

function printHelp() {
  process.stdout.write(
    [
      'Usage: node extract_usage_surface.mjs --project-root <path> --output <json>',
      '       [--entry <relative-file>] [--parser-root <node-project>]',
      '       [--contract <versioned-contract.json>] [--alias-config <tsconfig/vite alias JSON>]',
      '       [--changed-files <json-file>]',
      '       [--cache <resolver-cache.json>]',
      '',
      'The parser root must expose @babel/parser and, for .vue files, @vue/compiler-sfc.',
    ].join('\n') + '\n',
  )
}

function sha256Text(value) {
  return crypto.createHash('sha256').update(value).digest('hex')
}

function toPosix(value) {
  return value.split(path.sep).join('/')
}

function walk(node, visitor, parent = null) {
  if (!node || typeof node !== 'object') return
  if (typeof node.type === 'string') visitor(node, parent)
  for (const [key, value] of Object.entries(node)) {
    if (
      key === 'loc' ||
      key === 'start' ||
      key === 'end' ||
      key === 'extra' ||
      key === 'comments' ||
      key === 'tokens'
    ) continue
    if (Array.isArray(value)) {
      for (const child of value) walk(child, visitor, node)
    } else if (value && typeof value === 'object') {
      walk(value, visitor, node)
    }
  }
}

function collectSourceFiles(root) {
  const files = []
  const visit = (directory) => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      if (entry.isDirectory() && SKIP_DIRECTORIES.has(entry.name)) continue
      const fullPath = path.join(directory, entry.name)
      if (entry.isDirectory()) visit(fullPath)
      else if (entry.isFile() && SOURCE_EXTENSIONS.has(path.extname(entry.name).toLowerCase())) {
        if (!entry.name.toLowerCase().endsWith('.min.js')) files.push(fullPath)
      }
    }
  }
  visit(root)
  return files.sort()
}

function defaultEntries(projectRoot) {
  const entries = []
  const indexPath = path.join(projectRoot, 'index.html')
  if (fs.existsSync(indexPath)) {
    const html = fs.readFileSync(indexPath, 'utf8')
    const scriptPattern = /<script\b[^>]*\btype=["']module["'][^>]*\bsrc=["']([^"']+)["'][^>]*>/gi
    for (const match of html.matchAll(scriptPattern)) {
      const source = match[1].replace(/^\//, '')
      entries.push(path.resolve(projectRoot, source))
    }
  }
  for (const candidate of ['src/main.js', 'src/main.ts', 'src/main.jsx', 'src/main.tsx']) {
    const fullPath = path.join(projectRoot, candidate)
    if (fs.existsSync(fullPath)) entries.push(fullPath)
  }
  return [...new Set(entries)]
}

function parserPlugins(language, filename) {
  const plugins = [
    'classProperties',
    'classPrivateProperties',
    'classPrivateMethods',
    'decorators-legacy',
    'dynamicImport',
    'importAttributes',
    'optionalChaining',
    'topLevelAwait',
  ]
  const isTypeScript = language === 'ts' || /\.tsx?$/i.test(filename)
  const isJsx = language === 'tsx' || /\.[jt]sx$/i.test(filename)
  if (isTypeScript) plugins.push('typescript')
  if (isJsx) plugins.push('jsx')
  return plugins
}

function parseSegments(filename, source, babelParser, vueCompiler) {
  const extension = path.extname(filename).toLowerCase()
  const segments = []
  if (extension !== '.vue') {
    segments.push({ block: 'module', content: source, lineOffset: 0, language: extension.slice(1) })
  } else {
    if (!vueCompiler) throw new Error('@vue/compiler-sfc is required to parse .vue files.')
    const parsed = vueCompiler.parse(source, { filename })
    if (parsed.errors.length > 0) {
      throw new Error(parsed.errors.map((error) => String(error)).join('; '))
    }
    for (const [blockName, block] of [
      ['script', parsed.descriptor.script],
      ['script_setup', parsed.descriptor.scriptSetup],
    ]) {
      if (!block) continue
      segments.push({
        block: blockName,
        content: block.content,
        lineOffset: Math.max(0, block.loc.start.line - 1),
        language: block.lang || 'js',
      })
    }
  }

  return segments.map((segment) => ({
    ...segment,
    ast: babelParser.parse(segment.content, {
      sourceType: 'unambiguous',
      allowAwaitOutsideFunction: true,
      errorRecovery: false,
      plugins: parserPlugins(segment.language, filename),
    }),
  }))
}

function evaluateStaticString(node, constants) {
  if (!node) return null
  if (node.type === 'StringLiteral' || node.type === 'Literal' && typeof node.value === 'string') {
    return node.value
  }
  if (node.type === 'TemplateLiteral' && node.expressions.length === 0) {
    return node.quasis.map((quasi) => quasi.value.cooked ?? quasi.value.raw).join('')
  }
  if (node.type === 'BinaryExpression' && node.operator === '+') {
    const left = evaluateStaticString(node.left, constants)
    const right = evaluateStaticString(node.right, constants)
    return left === null || right === null ? null : `${left}${right}`
  }
  if (node.type === 'Identifier' && constants.has(node.name)) return constants.get(node.name)
  return null
}

function propertyName(node, constants) {
  if (!node.computed && (node.property.type === 'Identifier' || node.property.type === 'PrivateName')) {
    return node.property.name
  }
  return evaluateStaticString(node.property, constants)
}

function sameBinding(left, right) {
  return JSON.stringify(left) === JSON.stringify(right)
}

// 跨模块传播只比较可解析含义；provenance 差异不会把同一 ThingJS 引用误判为冲突。
function sameReferenceMeaning(left, right) {
  const stripProvenance = (value) => {
    if (!value || typeof value !== 'object') return value
    if (Array.isArray(value)) return value.map(stripProvenance)
    return Object.fromEntries(
      Object.entries(value)
        .filter(([key]) => key !== 'provenance')
        .map(([key, item]) => [key, stripProvenance(item)]),
    )
  }
  return sameBinding(stripProvenance(left), stripProvenance(right))
}

function cloneReference(reference) {
  if (!reference || typeof reference !== 'object') return reference
  return JSON.parse(JSON.stringify(reference))
}

function mergeReference(existing, incoming) {
  if (!existing) return cloneReference(incoming)
  if (sameReferenceMeaning(existing, incoming)) {
    return {
      ...cloneReference(existing),
      provenance: [...new Set([...(existing.provenance || []), ...(incoming?.provenance || [])])],
    }
  }
  return {
    type: 'ambiguous',
    provenance: [...new Set([...(existing.provenance || []), ...(incoming?.provenance || [])])],
  }
}

function referenceMapToObject(referenceMap) {
  return Object.fromEntries(
    [...referenceMap.entries()].map(([name, reference]) => [name, cloneReference(reference)]),
  )
}

function resolvedReferenceOwner(typeDescriptor) {
  if (!typeDescriptor || typeof typeDescriptor !== 'object') return null
  if (typeDescriptor.kind === 'reference' && typeof typeDescriptor.name === 'string') {
    return typeDescriptor.name.startsWith('THING.') ? typeDescriptor.name : null
  }
  if (typeDescriptor.kind === 'promise') return resolvedReferenceOwner(typeDescriptor.value)
  return null
}

function contractReturnOwner(contractIndex, owner, member, kind) {
  const record = contractIndex.get(`${kind}|${owner}|${member}`)
  if (!record || !Array.isArray(record.signatures)) return null
  for (const signature of record.signatures) {
    const resolvedOwner = resolvedReferenceOwner(signature?.return_type)
    if (resolvedOwner) return resolvedOwner
  }
  return null
}

function callReturnReference(callee, contractIndex) {
  if (callee?.type === 'instance_member') {
    const owner = callee.returnOwner || contractReturnOwner(
      contractIndex,
      callee.instanceOwner,
      callee.chain.at(-1),
      'method',
    )
    if (owner) {
      return {
        type: 'instance',
        owner,
        provenance: [...(callee.provenance || []), `return-owner:${owner}`],
      }
    }
  }
  if (callee?.type === 'namespace') {
    const segments = callee.path.split('.')
    if (segments.length > 2) {
      const owner = segments.slice(0, -1).join('.')
      const returnOwner = contractReturnOwner(contractIndex, owner, segments.at(-1), 'method')
      if (returnOwner) {
        return {
          type: 'instance',
          owner: returnOwner,
          provenance: [...(callee.provenance || []), `return-owner:${returnOwner}`],
        }
      }
    }
  }
  return null
}

function resolveInstanceMember(base, property, contractIndex) {
  const owner = base.type === 'instance' ? base.owner : base.returnOwner
  if (owner) {
    return {
      type: 'instance_member',
      instanceOwner: owner,
      chain: [property],
      returnOwner: contractReturnOwner(contractIndex, owner, property, 'property'),
      provenance: [
        ...(base.provenance || []),
        ...(base.type === 'instance_member' ? [`nested-owner:${owner}`] : []),
        `instance-member:${property}`,
      ],
    }
  }
  return {
    ...base,
    type: 'instance_member',
    chain: [...(base.chain || []), property],
    provenance: [...(base.provenance || []), `member:${property}`],
  }
}

function loadContractIndex(contractPath) {
  if (!contractPath) return new Map()
  const resolvedPath = path.resolve(contractPath)
  const contract = JSON.parse(fs.readFileSync(resolvedPath, 'utf8'))
  // Legacy text signatures are intentionally excluded: a resolver may consume
  // only the structured return type already accepted by the Contract validator.
  if (contract.schema_version !== 3 || contract.signature_schema_version !== 1) return new Map()
  const index = new Map()
  for (const record of contract.apis || []) {
    if (!record || !['existence_verified', 'behavior_verified'].includes(record.contract_state)) continue
    if (record.usage_state === 'blocked') continue
    if (!['method', 'property'].includes(record.kind)) continue
    if (typeof record.owner !== 'string' || typeof record.name !== 'string') continue
    if (!Array.isArray(record.signatures)) continue
    if (!record.signatures.some((signature) => signature && typeof signature.return_type === 'object')) continue
    index.set(`${record.kind}|${record.owner}|${record.name}`, record)
  }
  return index
}

function loadAliasEntries(aliasConfigPath) {
  if (!aliasConfigPath) return []
  const resolvedPath = path.resolve(aliasConfigPath)
  const config = JSON.parse(fs.readFileSync(resolvedPath, 'utf8'))
  const entries = []
  const add = (prefix, replacement, baseDirectory = path.dirname(resolvedPath)) => {
    if (typeof prefix !== 'string' || typeof replacement !== 'string') return
    const wildcard = prefix.endsWith('*')
    const normalizedPrefix = wildcard ? prefix.slice(0, -1) : prefix.endsWith('/') ? prefix : `${prefix}/`
    const normalizedReplacement = wildcard ? replacement.replace(/\*$/, '') : replacement.endsWith('/') ? replacement : `${replacement}/`
    entries.push({ prefix: normalizedPrefix, replacement: path.resolve(baseDirectory, normalizedReplacement) })
  }
  const paths = config.compilerOptions?.paths
  const pathBase = config.compilerOptions?.baseUrl
    ? path.resolve(path.dirname(resolvedPath), config.compilerOptions.baseUrl)
    : path.dirname(resolvedPath)
  if (paths && typeof paths === 'object') {
    for (const [prefix, replacements] of Object.entries(paths)) {
      const first = Array.isArray(replacements) ? replacements[0] : replacements
      if (typeof first === 'string') add(prefix, first, pathBase)
    }
  }
  const aliases = config.resolve?.alias ?? config.aliases
  if (Array.isArray(aliases)) {
    for (const alias of aliases) add(alias?.find, alias?.replacement)
  } else if (aliases && typeof aliases === 'object') {
    for (const [prefix, replacement] of Object.entries(aliases)) add(prefix, replacement)
  }
  return entries.sort((left, right) => right.prefix.length - left.prefix.length)
}

function setBinding(bindings, name, value) {
  if (!name || !value) return false
  const previous = bindings.get(name)
  if (!previous) {
    bindings.set(name, value)
    return true
  }
  if (sameBinding(previous, value)) return false
  if (previous.type !== 'ambiguous') {
    bindings.set(name, {
      type: 'ambiguous',
      provenance: [...new Set([...(previous.provenance || []), ...(value.provenance || [])])],
    })
    return true
  }
  return false
}

function resolveReference(node, bindings, constants, contractIndex) {
  if (!node) return null
  if (node.type === 'Identifier') {
    if (node.name === 'THING') return { type: 'namespace', path: 'THING', provenance: ['global:THING'] }
    return bindings.get(node.name) || null
  }
  if (node.type === 'TSAsExpression' || node.type === 'TSTypeAssertion' || node.type === 'ParenthesizedExpression') {
    return resolveReference(node.expression, bindings, constants, contractIndex)
  }
  if (node.type === 'NewExpression') {
    const callee = resolveReference(node.callee, bindings, constants, contractIndex)
    if (callee?.type === 'namespace') {
      return {
        type: 'instance',
        owner: callee.path,
        provenance: [...callee.provenance, `construct:${callee.path}`],
      }
    }
    return callee?.type === 'ambiguous' ? callee : null
  }
  if (node.type === 'CallExpression' || node.type === 'OptionalCallExpression') {
    const callee = resolveReference(node.callee, bindings, constants, contractIndex)
    return callReturnReference(callee, contractIndex)
  }
  if (node.type !== 'MemberExpression' && node.type !== 'OptionalMemberExpression') return null

  const base = resolveReference(node.object, bindings, constants, contractIndex)
  if (!base) return null
  if (base.type === 'ambiguous') return base
  const property = propertyName(node, constants)
  if (property === null) {
    return {
      type: 'dynamic',
      base,
      provenance: [...(base.provenance || []), 'computed:unresolved'],
    }
  }
  if (base.type === 'namespace') {
    return {
      type: 'namespace',
      path: `${base.path}.${property}`,
      provenance: [...base.provenance, `member:${property}`],
    }
  }
  if (base.type === 'instance') {
    return resolveInstanceMember(base, property, contractIndex)
  }
  if (base.type === 'instance_member') {
    return resolveInstanceMember(base, property, contractIndex)
  }
  if (base.type === 'module_namespace') {
    const exported = base.exports?.[property]
    if (!exported) return null
    return {
      ...cloneReference(exported),
      provenance: [
        ...(base.provenance || []),
        `module-namespace:${property}`,
        ...(exported.provenance || []),
      ],
    }
  }
  return base.type === 'dynamic' ? base : null
}

function collectBindings(ast, constants, contractIndex, initialBindings = new Map()) {
  const bindings = new Map(
    [...initialBindings.entries()].map(([name, reference]) => [name, cloneReference(reference)]),
  )
  const declarations = []
  const assignments = []
  walk(ast, (node) => {
    if (node.type === 'VariableDeclarator') declarations.push(node)
    if (node.type === 'AssignmentExpression' && node.left.type === 'Identifier') assignments.push(node)
  })

  // 多轮收敛允许 `const T = THING; const App = T.App` 这类别名链。
  for (let pass = 0; pass < 8; pass += 1) {
    let changed = false
    for (const declaration of declarations) {
      const resolved = resolveReference(declaration.init, bindings, constants, contractIndex)
      if (!resolved) continue
      if (declaration.id.type === 'Identifier') {
        changed = setBinding(
          bindings,
          declaration.id.name,
          { ...resolved, provenance: [...(resolved.provenance || []), `alias:${declaration.id.name}`] },
        ) || changed
      } else if (declaration.id.type === 'ObjectPattern') {
        for (const property of declaration.id.properties) {
          if (property.type !== 'ObjectProperty' || property.value.type !== 'Identifier') continue
          const key = property.computed
            ? evaluateStaticString(property.key, constants)
            : property.key.name || property.key.value
          if (!key) continue
          let memberBinding = null
          if (resolved.type === 'namespace') {
            memberBinding = { type: 'namespace', path: `${resolved.path}.${key}` }
          } else if (resolved.type === 'instance') {
            memberBinding = {
              type: 'instance_member',
              instanceOwner: resolved.owner,
              chain: [key],
              returnOwner: contractReturnOwner(contractIndex, resolved.owner, key, 'property'),
            }
          } else if (resolved.type === 'instance_member') {
            memberBinding = resolveInstanceMember(resolved, key, contractIndex)
          }
          if (!memberBinding) continue
          changed = setBinding(bindings, property.value.name, {
            ...memberBinding,
            provenance: [...resolved.provenance, `destructure:${key}->${property.value.name}`],
          }) || changed
        }
      }
    }
    for (const assignment of assignments) {
      const resolved = resolveReference(assignment.right, bindings, constants, contractIndex)
      if (resolved) changed = setBinding(bindings, assignment.left.name, resolved) || changed
    }
    if (!changed) break
  }
  return bindings
}

function collectTopLevelBindings(ast, constants, contractIndex, initialBindings) {
  const body = []
  for (const statement of ast.program.body) {
    if (statement.type === 'VariableDeclaration') body.push(statement)
    if (
      statement.type === 'ExportNamedDeclaration' &&
      statement.declaration?.type === 'VariableDeclaration'
    ) body.push(statement.declaration)
  }
  return collectBindings({ type: 'Program', body }, constants, contractIndex, initialBindings)
}

function exportedName(node) {
  if (!node) return null
  if (node.type === 'Identifier') return node.name
  if (node.type === 'StringLiteral' || node.type === 'Literal') return node.value
  return null
}

// 只追踪静态 return 已能回溯到 ThingJS 的导出函数，避免普通业务工具函数制造伪 Usage Entity。
function functionMayReturnThingReference(node, bindings, constants, contractIndex) {
  const returns = []
  if (node.body?.type === 'BlockStatement') {
    walk(node.body, (candidate) => {
      if (candidate.type === 'ReturnStatement' && candidate.argument) returns.push(candidate.argument)
    })
  } else if (node.body) {
    returns.push(node.body)
  }
  return returns.some((value) => {
    const reference = resolveReference(value, bindings, constants, contractIndex)
    return ['namespace', 'instance', 'instance_member', 'dynamic', 'ambiguous'].includes(reference?.type)
  })
}

function collectExportBindings(ast, bindings, constants, contractIndex, importedExports) {
  const exports = new Map()
  const add = (name, reference) => {
    if (typeof name !== 'string' || !reference) return
    exports.set(name, mergeReference(exports.get(name), reference))
  }
  const unresolvedFunction = (name, provenance) => ({
    type: 'unresolved_cross_module_function',
    crossModuleFunction: true,
    provenance: [provenance || `export-function:${name}`],
  })

  for (const statement of ast.program.body) {
    if (statement.type === 'ExportNamedDeclaration') {
      if (statement.declaration?.type === 'VariableDeclaration') {
        for (const declaration of statement.declaration.declarations) {
          if (declaration.id.type !== 'Identifier') continue
          const reference = (declaration.init?.type === 'FunctionExpression'
            || declaration.init?.type === 'ArrowFunctionExpression')
            && functionMayReturnThingReference(declaration.init, bindings, constants, contractIndex)
            ? unresolvedFunction(declaration.id.name)
            : bindings.get(declaration.id.name)
          add(declaration.id.name, reference)
        }
      }
      if (
        statement.declaration?.type === 'FunctionDeclaration'
        && statement.declaration.id?.name
        && functionMayReturnThingReference(statement.declaration, bindings, constants, contractIndex)
      ) {
        add(statement.declaration.id.name, unresolvedFunction(statement.declaration.id.name))
      }
      for (const specifier of statement.specifiers || []) {
        const localName = exportedName(specifier.local)
        const name = exportedName(specifier.exported)
        const reference = statement.source
          ? importedExports.get(exportedName(specifier.local))
          : bindings.get(localName)
        if (reference) add(name, reference)
      }
    }
    if (statement.type === 'ExportDefaultDeclaration') {
      const declaration = statement.declaration
      const reference = (declaration?.type === 'FunctionDeclaration'
        || declaration?.type === 'FunctionExpression'
        || declaration?.type === 'ArrowFunctionExpression')
        && functionMayReturnThingReference(declaration, bindings, constants, contractIndex)
        ? unresolvedFunction('default', 'export-function:default')
        : declaration?.type === 'Identifier'
        ? bindings.get(declaration.name)
        : resolveReference(declaration, bindings, constants, contractIndex)
      if (reference) add('default', reference)
    }
  }
  return exports
}

function collectImportedBindings(ast, projectRoot, filename, sourceSet, aliasEntries, moduleExports) {
  const bindings = new Map()
  const importSources = []
  const add = (name, reference) => {
    if (!name || !reference) return
    bindings.set(name, mergeReference(bindings.get(name), reference))
  }

  for (const statement of ast.program.body) {
    if (statement.type !== 'ImportDeclaration' || typeof statement.source?.value !== 'string') continue
    const specifier = statement.source.value
    importSources.push(specifier)
    const target = resolveImport(projectRoot, filename, specifier, sourceSet, aliasEntries)
    const targetExports = target ? moduleExports.get(path.normalize(target)) : null
    if (!targetExports) continue
    for (const item of statement.specifiers || []) {
      if (item.type === 'ImportSpecifier') {
        const imported = exportedName(item.imported)
        const reference = targetExports.get(imported)
        if (reference) {
          add(item.local.name, {
            ...cloneReference(reference),
            provenance: [...(reference.provenance || []), `import:${specifier}:${imported}`],
          })
        }
      } else if (item.type === 'ImportDefaultSpecifier') {
        const reference = targetExports.get('default')
        if (reference) {
          add(item.local.name, {
            ...cloneReference(reference),
            provenance: [...(reference.provenance || []), `import:${specifier}:default`],
          })
        }
      } else if (item.type === 'ImportNamespaceSpecifier') {
        add(item.local.name, {
          type: 'module_namespace',
          exports: referenceMapToObject(targetExports),
          provenance: [`import-namespace:${specifier}`],
        })
      }
    }
  }

  walk(ast, (node) => {
    if (node.type !== 'VariableDeclarator' || node.id.type !== 'Identifier') return
    const expression = node.init?.type === 'AwaitExpression' ? node.init.argument : node.init
    if (
      expression?.type !== 'CallExpression' ||
      expression.callee?.type !== 'Import' ||
      expression.arguments.length !== 1
    ) return
    const specifier = expression.arguments[0]?.value
    if (typeof specifier !== 'string') return
    const target = resolveImport(projectRoot, filename, specifier, sourceSet, aliasEntries)
    const targetExports = target ? moduleExports.get(path.normalize(target)) : null
    if (!targetExports || targetExports.size === 0) return
    add(node.id.name, {
      type: 'ambiguous',
      provenance: [`dynamic-import-value-flow:${specifier}`],
    })
  })
  return { bindings, importSources }
}

// `export *` 或显式 re-export 的同名冲突必须合并为 ambiguous，不能按遍历顺序放行。
function collectReExportBindings(ast, projectRoot, filename, sourceSet, aliasEntries, moduleExports) {
  const bindings = new Map()
  const add = (name, reference) => {
    if (!name || !reference) return
    bindings.set(name, mergeReference(bindings.get(name), reference))
  }

  for (const statement of ast.program.body) {
    if (!statement.source || typeof statement.source.value !== 'string') continue
    const target = resolveImport(projectRoot, filename, statement.source.value, sourceSet, aliasEntries)
    const targetExports = target ? moduleExports.get(path.normalize(target)) : null
    if (!targetExports) continue
    if (statement.type === 'ExportAllDeclaration') {
      for (const [name, reference] of targetExports.entries()) {
        if (name !== 'default') add(name, reference)
      }
      continue
    }
    if (statement.type !== 'ExportNamedDeclaration') continue
    for (const specifier of statement.specifiers || []) {
      const imported = exportedName(specifier.local)
      const exported = exportedName(specifier.exported)
      const reference = targetExports.get(imported)
      if (reference) add(exported, reference)
    }
  }
  return bindings
}

function collectModuleReferences(ast, projectRoot, filename, sourceSet, aliasEntries, moduleExports) {
  const bindings = collectImportedBindings(ast, projectRoot, filename, sourceSet, aliasEntries, moduleExports).bindings
  for (const [name, reference] of collectReExportBindings(ast, projectRoot, filename, sourceSet, aliasEntries, moduleExports)) {
    bindings.set(name, mergeReference(bindings.get(name), reference))
  }
  return bindings
}

function loadChangedFiles(changedFilesPath, projectRoot, sourceSet) {
  if (!changedFilesPath) return null
  const payload = JSON.parse(fs.readFileSync(path.resolve(changedFilesPath), 'utf8'))
  const values = Array.isArray(payload) ? payload : payload?.files
  if (!Array.isArray(values)) throw new Error('--changed-files JSON must be an array or an object with a files array.')
  const changed = new Set()
  for (const value of values) {
    if (typeof value !== 'string') throw new Error('--changed-files entries must be strings.')
    const resolved = path.normalize(path.isAbsolute(value) ? value : path.resolve(projectRoot, value))
    if (!sourceSet.has(resolved)) throw new Error(`--changed-files entry is not a source file: ${value}`)
    changed.add(resolved)
  }
  return changed
}

function resolverConfigurationSignature(args, projectRoot, requestedEntries) {
  const readSignatureInput = (filename) => {
    if (!filename) return null
    const resolved = path.resolve(filename)
    return fs.existsSync(resolved) ? sha256Text(fs.readFileSync(resolved, 'utf8')) : `missing:${resolved}`
  }
  return sha256Text(JSON.stringify({
    resolver: 'thingjs-usage-resolver-v2-cache-1',
    project_root: projectRoot,
    contract: readSignatureInput(args.contract),
    alias_config: readSignatureInput(args.aliasConfig),
    entries: requestedEntries.map((entry) => toPosix(path.relative(projectRoot, entry))).sort(),
  }))
}

function readResolverCache(cachePath, projectRoot, configurationSignature) {
  if (!cachePath) return { state: 'disabled', cache: null, reason: null }
  if (!fs.existsSync(cachePath)) return { state: 'miss', cache: null, reason: 'cache_missing' }
  try {
    const cache = JSON.parse(fs.readFileSync(cachePath, 'utf8'))
    if (
      cache.schema_version !== 1
      || cache.project_root !== projectRoot
      || cache.configuration_signature !== configurationSignature
      || !cache.files
      || !cache.surface
    ) return { state: 'miss', cache: null, reason: 'cache_identity_mismatch' }
    return { state: 'valid', cache, reason: null }
  } catch (error) {
    return { state: 'miss', cache: null, reason: 'cache_parse_failed' }
  }
}

function writeResolverCache(cachePath, projectRoot, configurationSignature, fileHashes, surface) {
  if (!cachePath || surface.incremental?.complete_surface !== true) return
  fs.mkdirSync(path.dirname(cachePath), { recursive: true })
  fs.writeFileSync(cachePath, JSON.stringify({
    schema_version: 1,
    project_root: projectRoot,
    configuration_signature: configurationSignature,
    files: fileHashes,
    surface,
  }, null, 2) + '\n', 'utf8')
}

function collectConstants(ast) {
  const constants = new Map()
  const declarations = []
  walk(ast, (node, parent) => {
    if (node.type === 'VariableDeclarator' && parent?.kind === 'const' && node.id.type === 'Identifier') {
      declarations.push(node)
    }
  })
  for (let pass = 0; pass < 8; pass += 1) {
    let changed = false
    for (const declaration of declarations) {
      const value = evaluateStaticString(declaration.init, constants)
      if (value !== null && constants.get(declaration.id.name) !== value) {
        constants.set(declaration.id.name, value)
        changed = true
      }
    }
    if (!changed) break
  }
  return constants
}

function argumentKind(argument) {
  if (!argument) return 'missing'
  if (argument.type === 'SpreadElement') return 'spread'
  if (argument.type === 'ObjectExpression') {
    const properties = argument.properties
      .filter((property) => property.type === 'ObjectProperty' || property.type === 'ObjectMethod')
      .map((property) => property.key?.name ?? property.key?.value)
      .filter(Boolean)
      .sort()
    return { kind: 'object', properties }
  }
  if (argument.type === 'ArrayExpression') return { kind: 'array', length: argument.elements.length }
  if (argument.type.endsWith('Literal')) return { kind: 'literal', value_type: typeof argument.value }
  if (argument.type === 'Identifier') return { kind: 'identifier', name: argument.name }
  if (argument.type === 'ArrowFunctionExpression' || argument.type === 'FunctionExpression') return 'function'
  return argument.type
}

function accessContext(node, parent) {
  if (parent?.type === 'NewExpression' && parent.callee === node) {
    return { accessType: 'construct', operationNode: parent, args: parent.arguments }
  }
  if ((parent?.type === 'CallExpression' || parent?.type === 'OptionalCallExpression') && parent.callee === node) {
    return { accessType: 'call', operationNode: parent, args: parent.arguments }
  }
  if (parent?.type === 'AssignmentExpression' && parent.left === node) {
    return { accessType: 'write', operationNode: parent, args: [] }
  }
  if (parent?.type === 'UpdateExpression') {
    return { accessType: 'update', operationNode: parent, args: [] }
  }
  return { accessType: 'read', operationNode: node, args: [] }
}

function canonicalShape(reference, accessType) {
  if (!reference) return null
  if (reference.type === 'ambiguous') {
    return { resolutionStatus: 'ambiguous', canonicalOwner: null, member: null, accessPath: [] }
  }
  if (reference.type === 'dynamic') {
    const baseOwner = reference.base.path || reference.base.owner || reference.base.instanceOwner || null
    return {
      resolutionStatus: 'dynamic_unresolved',
      canonicalOwner: baseOwner,
      member: null,
      accessPath: [],
    }
  }
  if (reference.type === 'namespace') {
    const segments = reference.path.split('.')
    if (accessType === 'construct') {
      return {
        resolutionStatus: 'resolved',
        canonicalOwner: reference.path,
        member: 'constructor',
        accessPath: [],
      }
    }
    return {
      resolutionStatus: 'resolved',
      canonicalOwner: segments.slice(0, -1).join('.'),
      member: segments.at(-1),
      accessPath: [segments.at(-1)],
    }
  }
  if (reference.type === 'instance_member') {
    return {
      resolutionStatus: reference.chain.length === 1 ? 'resolved' : 'ambiguous',
      canonicalOwner: reference.instanceOwner,
      member: reference.chain.at(-1),
      accessPath: reference.chain,
    }
  }
  return null
}

function unresolvedCallReference(node, bindings, constants) {
  if (node?.type !== 'CallExpression' && node?.type !== 'OptionalCallExpression') return null
  if (node.callee?.type !== 'Identifier') return null
  const binding = bindings.get(node.callee.name)
  if (!binding?.crossModuleFunction) return null
  return {
    type: 'ambiguous',
    provenance: [...(binding.provenance || []), `cross-module-call:${node.callee.name}`],
  }
}

function entityKind(accessType) {
  if (accessType === 'construct') return 'constructor'
  if (accessType === 'call') return 'method'
  return 'property'
}

function buildUsageEntity({ filename, relativePath, segment, node, parent, reference, source }) {
  const context = accessContext(node, parent)
  const shape = canonicalShape(reference, context.accessType)
  if (!shape || !RESOLUTION_STATES.has(shape.resolutionStatus)) return null
  const location = node.loc?.start || { line: 1, column: 0 }
  const line = location.line + segment.lineOffset
  const column = location.column + 1
  const expression = source.slice(context.operationNode.start, context.operationNode.end).trim()
  const kind = entityKind(context.accessType)
  const canonicalKey = shape.canonicalOwner && shape.member
    ? `${kind}|${shape.canonicalOwner}|${shape.member}`
    : null
  const idSeed = `${relativePath}|${segment.block}|${line}|${column}|${expression}|${canonicalKey || shape.resolutionStatus}`
  return {
    id: `usage-${sha256Text(idSeed).slice(0, 16)}`,
    canonical_key: canonicalKey,
    canonical_owner: shape.canonicalOwner,
    member: shape.member,
    access_path: shape.accessPath,
    access_type: context.accessType,
    argument_shape: {
      count: context.args.length,
      arguments: context.args.map(argumentKind),
    },
    source: {
      path: relativePath,
      line,
      column,
      block: segment.block,
    },
    expression,
    alias_provenance: [...new Set(reference.provenance || [])],
    resolution_status: shape.resolutionStatus,
    production_reachable: false,
  }
}

function isNestedMemberObject(node, parent) {
  return (
    (parent?.type === 'MemberExpression' || parent?.type === 'OptionalMemberExpression') &&
    parent.object === node
  )
}

function collectSegmentImports(relativePath, segment, constants) {
  const imports = []
  const unresolvedImports = []
  const recordDynamicImportGap = (node, reason) => {
    const location = node.loc?.start || { line: 1, column: 0 }
    unresolvedImports.push({
      specifier: null,
      reason,
      source: {
        path: relativePath,
        line: location.line + segment.lineOffset,
        column: location.column + 1,
        block: segment.block,
      },
    })
  }

  walk(segment.ast, (node, parent) => {
    if (
      node.type === 'ImportDeclaration' ||
      node.type === 'ExportAllDeclaration' ||
      node.type === 'ExportNamedDeclaration' && node.source
    ) {
      if (typeof node.source?.value === 'string') imports.push(node.source.value)
    }
    if (node.type === 'CallExpression' && node.callee?.type === 'Import' && node.arguments.length === 1) {
      const value = evaluateStaticString(node.arguments[0], constants)
      if (value !== null) imports.push(value)
      else recordDynamicImportGap(node, 'dynamic_import_specifier')
    }
    if (node.type === 'CallExpression' && node.callee?.type === 'Identifier' && node.callee.name === 'require' && node.arguments.length === 1) {
      const value = evaluateStaticString(node.arguments[0], constants)
      if (value !== null) imports.push(value)
      else recordDynamicImportGap(node, 'dynamic_require_specifier')
    }
  })
  return { imports, unresolvedImports }
}

function analyzeSegment(filename, relativePath, segment, contractIndex, initialBindings = new Map()) {
  const constants = collectConstants(segment.ast)
  const bindings = collectBindings(segment.ast, constants, contractIndex, initialBindings)
  const entities = []
  const { imports, unresolvedImports } = collectSegmentImports(relativePath, segment, constants)

  walk(segment.ast, (node, parent) => {
    const isMember = node.type === 'MemberExpression' || node.type === 'OptionalMemberExpression'
    if (isMember) {
      if (isNestedMemberObject(node, parent)) return
      let reference = resolveReference(node, bindings, constants, contractIndex)
      if (!reference && (node.object.type === 'CallExpression' || node.object.type === 'OptionalCallExpression')) {
        reference = unresolvedCallReference(node.object, bindings, constants)
      }
      const entity = buildUsageEntity({
        filename,
        relativePath,
        segment,
        node,
        parent,
        reference,
        source: segment.content,
      })
      if (entity) entities.push(entity)
      return
    }

    // `new AppAlias()` 没有 MemberExpression，需要从别名绑定补出构造使用。
    if (node.type === 'NewExpression' && node.callee.type === 'Identifier') {
      const reference = resolveReference(node.callee, bindings, constants, contractIndex)
      if (!reference || !['namespace', 'ambiguous', 'dynamic'].includes(reference.type)) return
      const syntheticParent = { type: 'NewExpression', callee: node.callee, arguments: node.arguments }
      syntheticParent.start = node.start
      syntheticParent.end = node.end
      const entity = buildUsageEntity({
        filename,
        relativePath,
        segment,
        node: node.callee,
        parent: syntheticParent,
        reference,
        source: segment.content,
      })
      if (entity) entities.push(entity)
    }

    // 方法/函数从 THING owner 上解构或赋值为本地别名后，调用点仍需回溯原 owner。
    if (node.type === 'CallExpression' && node.callee.type === 'Identifier') {
      const reference = resolveReference(node.callee, bindings, constants, contractIndex)
      if (!reference || !['namespace', 'instance_member', 'dynamic', 'ambiguous'].includes(reference.type)) return
      const syntheticParent = { type: 'CallExpression', callee: node.callee, arguments: node.arguments }
      syntheticParent.start = node.start
      syntheticParent.end = node.end
      const entity = buildUsageEntity({
        filename,
        relativePath,
        segment,
        node: node.callee,
        parent: syntheticParent,
        reference,
        source: segment.content,
      })
      if (entity) entities.push(entity)
    }
  })

  return { entities, imports, unresolvedImports }
}

function isProjectImport(specifier) {
  return specifier.startsWith('.') || specifier.startsWith('/') || specifier.startsWith('@/') || specifier.startsWith('~/')
}

function isAnalyzableSourceImport(specifier) {
  const cleanSpecifier = specifier.split(/[?#]/, 1)[0]
  const extension = path.extname(cleanSpecifier).toLowerCase()
  return extension === '' || SOURCE_EXTENSIONS.has(extension)
}

function resolveImport(projectRoot, fromFile, specifier, sourceSet, aliasEntries) {
  const configuredAlias = aliasEntries.find((entry) => specifier === entry.prefix.slice(0, -1) || specifier.startsWith(entry.prefix))
  if ((!isProjectImport(specifier) && !configuredAlias) || !isAnalyzableSourceImport(specifier)) return null
  const cleanSpecifier = specifier.split(/[?#]/, 1)[0]
  let base
  const cleanConfiguredAlias = aliasEntries.find((entry) => cleanSpecifier === entry.prefix.slice(0, -1) || cleanSpecifier.startsWith(entry.prefix))
  if (cleanConfiguredAlias) base = path.resolve(cleanConfiguredAlias.replacement, cleanSpecifier.slice(cleanConfiguredAlias.prefix.length))
  else if (cleanSpecifier.startsWith('@/')) base = path.resolve(projectRoot, 'src', cleanSpecifier.slice(2))
  else if (cleanSpecifier.startsWith('~/')) base = path.resolve(projectRoot, cleanSpecifier.slice(2))
  else if (cleanSpecifier.startsWith('/')) base = path.resolve(projectRoot, cleanSpecifier.slice(1))
  else base = path.resolve(path.dirname(fromFile), cleanSpecifier)
  const candidates = [base]
  for (const extension of SOURCE_EXTENSIONS) candidates.push(`${base}${extension}`)
  for (const extension of SOURCE_EXTENSIONS) candidates.push(path.join(base, `index${extension}`))
  return candidates.find((candidate) => sourceSet.has(path.normalize(candidate))) || null
}

function computeReachable(entries, importGraph) {
  const reachable = new Set()
  const queue = entries.filter((entry) => importGraph.has(path.normalize(entry))).map(path.normalize)
  while (queue.length > 0) {
    const current = queue.shift()
    if (reachable.has(current)) continue
    reachable.add(current)
    for (const dependency of importGraph.get(current) || []) {
      if (!reachable.has(dependency)) queue.push(dependency)
    }
  }
  return reachable
}

function computeIncrementalFiles(changedFiles, importGraph) {
  if (!changedFiles) return null
  const reverseGraph = new Map([...importGraph.keys()].map((file) => [file, []]))
  for (const [importer, dependencies] of importGraph.entries()) {
    for (const dependency of dependencies) reverseGraph.get(dependency)?.push(importer)
  }
  const affected = new Set()
  const queue = [...changedFiles]
  while (queue.length > 0) {
    const current = queue.shift()
    if (affected.has(current)) continue
    affected.add(current)
    for (const importer of reverseGraph.get(current) || []) {
      if (!affected.has(importer)) queue.push(importer)
    }
  }
  return affected
}

function regexDiscoveries(relativePath, source, reason) {
  return [...source.matchAll(THING_TOKEN_PATTERN)].map((match) => ({
    token: match[0],
    source: { path: relativePath, offset: match.index },
    reason,
    classification: 'discovery_only',
  }))
}

function main() {
  const args = parseArgs(process.argv.slice(2))
  if (args.help) {
    printHelp()
    return 0
  }
  if (!args.projectRoot || !args.output) {
    printHelp()
    return 2
  }

  const projectRoot = path.resolve(args.projectRoot)
  const parserRoot = path.resolve(args.parserRoot || projectRoot)
  const contractIndex = loadContractIndex(args.contract)
  const aliasEntries = loadAliasEntries(args.aliasConfig)
  const projectRequire = createRequire(path.join(parserRoot, 'package.json'))
  const babelParser = projectRequire('@babel/parser')
  let vueCompiler = null
  try {
    vueCompiler = projectRequire('@vue/compiler-sfc')
  } catch (error) {
    // 非 Vue 项目不需要该依赖；遇到 .vue 时 parse failure 会进入 discovery。
  }

  const files = collectSourceFiles(projectRoot)
  const sourceSet = new Set(files.map(path.normalize))
  const changedFiles = loadChangedFiles(args.changedFiles, projectRoot, sourceSet)
  const requestedEntries = args.entries.length > 0
    ? args.entries.map((entry) => path.resolve(projectRoot, entry))
    : defaultEntries(projectRoot)
  const fileHashes = Object.fromEntries(files.map((file) => [
    toPosix(path.relative(projectRoot, file)),
    sha256Text(fs.readFileSync(file, 'utf8')),
  ]))
  const configurationSignature = resolverConfigurationSignature(args, projectRoot, requestedEntries)
  const cachePath = args.cache ? path.resolve(args.cache) : null
  const cacheResult = readResolverCache(cachePath, projectRoot, configurationSignature)
  const cacheInvalidatedFiles = new Set()
  if (cacheResult.cache) {
    for (const relativePath of Object.keys(fileHashes)) {
      if (cacheResult.cache.files[relativePath] !== fileHashes[relativePath]) {
        cacheInvalidatedFiles.add(relativePath)
      }
    }
    for (const relativePath of Object.keys(cacheResult.cache.files)) {
      if (!Object.prototype.hasOwnProperty.call(fileHashes, relativePath)) cacheInvalidatedFiles.add(relativePath)
    }
  } else if (cachePath) {
    for (const relativePath of Object.keys(fileHashes)) cacheInvalidatedFiles.add(relativePath)
  }
  if (cacheResult.state === 'valid' && !changedFiles && cacheInvalidatedFiles.size === 0) {
    const cachedSurface = JSON.parse(JSON.stringify(cacheResult.cache.surface))
    cachedSurface.generated_at = new Date().toISOString()
    cachedSurface.cache = {
      enabled: true,
      hit: true,
      invalidated_files: [],
      reused_files: Object.keys(fileHashes).sort(),
      reason: 'content_and_configuration_match',
    }
    const cachedOutput = path.resolve(args.output)
    fs.mkdirSync(path.dirname(cachedOutput), { recursive: true })
    fs.writeFileSync(cachedOutput, JSON.stringify(cachedSurface, null, 2) + '\n', 'utf8')
    process.stdout.write(JSON.stringify(cachedSurface.summary, null, 2) + '\n')
    return 0
  }
  const importGraph = new Map(files.map((file) => [path.normalize(file), []]))
  const moduleRecords = new Map()
  const moduleExports = new Map()
  const usageEntities = []
  const parseFailures = []
  const discoveryFindings = []
  const reachabilityGaps = []

  for (const filename of files) {
    const relativePath = toPosix(path.relative(projectRoot, filename))
    const source = fs.readFileSync(filename, 'utf8')
    let segments
    try {
      segments = parseSegments(filename, source, babelParser, vueCompiler)
    } catch (error) {
      parseFailures.push({
        path: relativePath,
        resolution_status: 'parse_failed',
        error: String(error.message || error),
      })
      discoveryFindings.push(...regexDiscoveries(relativePath, source, 'parse_failure'))
      continue
    }

    moduleRecords.set(path.normalize(filename), { filename, relativePath, source, segments })
    for (const segment of segments) {
      const analysis = collectSegmentImports(relativePath, segment, collectConstants(segment.ast))
      for (const specifier of analysis.imports) {
        const resolved = resolveImport(projectRoot, filename, specifier, sourceSet, aliasEntries)
        if (resolved) importGraph.get(path.normalize(filename)).push(path.normalize(resolved))
        else if ((isProjectImport(specifier) || aliasEntries.some((entry) => specifier.startsWith(entry.prefix))) && isAnalyzableSourceImport(specifier)) {
          reachabilityGaps.push({
            specifier,
            reason: 'local_import_unresolved',
            source: { path: relativePath, block: segment.block },
          })
        }
      }
      reachabilityGaps.push(...analysis.unresolvedImports)
    }
  }

  for (const record of moduleRecords.values()) moduleExports.set(path.normalize(record.filename), new Map())

  // 固定轮次覆盖常见 re-export 链；超过边界的循环不会被当作已证明的 ThingJS alias。
  let moduleFlowConverged = false
  for (let pass = 0; pass < 8; pass += 1) {
    let changed = false
    for (const record of moduleRecords.values()) {
      const nextExports = new Map(moduleExports.get(path.normalize(record.filename)) || [])
      for (const segment of record.segments) {
        const imported = collectImportedBindings(
          segment.ast,
          projectRoot,
          record.filename,
          sourceSet,
          aliasEntries,
          moduleExports,
        )
        const constants = collectConstants(segment.ast)
        const bindings = collectTopLevelBindings(segment.ast, constants, contractIndex, imported.bindings)
        const direct = collectExportBindings(segment.ast, bindings, constants, contractIndex, imported.bindings)
        const reExports = collectReExportBindings(
          segment.ast,
          projectRoot,
          record.filename,
          sourceSet,
          aliasEntries,
          moduleExports,
        )
        const stageExports = new Map()
        for (const [name, reference] of [...direct, ...reExports]) {
          stageExports.set(name, mergeReference(stageExports.get(name), reference))
        }
        for (const [name, reference] of stageExports) {
          const merged = mergeReference(nextExports.get(name), reference)
          if (!sameBinding(nextExports.get(name), merged)) {
            nextExports.set(name, merged)
            changed = true
          }
        }
      }
      if (!sameBinding(
        referenceMapToObject(moduleExports.get(path.normalize(record.filename))),
        referenceMapToObject(nextExports),
      )) changed = true
      moduleExports.set(path.normalize(record.filename), nextExports)
    }
    if (!changed) {
      moduleFlowConverged = true
      break
    }
  }

  const incrementalFiles = computeIncrementalFiles(changedFiles, importGraph)
  const coveredByFile = new Map()
  for (const record of moduleRecords.values()) {
    if (incrementalFiles && !incrementalFiles.has(path.normalize(record.filename))) continue
    for (const segment of record.segments) {
      const moduleReferences = collectModuleReferences(
        segment.ast,
        projectRoot,
        record.filename,
        sourceSet,
        aliasEntries,
        moduleExports,
      )
      const analysis = analyzeSegment(
        record.filename,
        record.relativePath,
        segment,
        contractIndex,
        moduleReferences,
      )
      usageEntities.push(...analysis.entities)
      const coveredTokens = coveredByFile.get(record.filename) || new Set()
      for (const entity of analysis.entities) {
        for (const token of entity.expression.match(THING_TOKEN_PATTERN) || []) coveredTokens.add(token)
      }
      coveredByFile.set(record.filename, coveredTokens)
    }
    for (const finding of regexDiscoveries(record.relativePath, record.source, 'unmodeled_pattern')) {
      if (!(coveredByFile.get(record.filename) || new Set()).has(finding.token)) discoveryFindings.push(finding)
    }
  }

  const reachable = computeReachable(requestedEntries, importGraph)
  for (const entity of usageEntities) {
    const absolute = path.normalize(path.resolve(projectRoot, entity.source.path))
    entity.production_reachable = reachable.has(absolute)
  }
  for (const gap of reachabilityGaps) {
    const absolute = path.normalize(path.resolve(projectRoot, gap.source.path))
    gap.production_reachable = reachable.has(absolute)
  }
  if (!moduleFlowConverged) {
    reachabilityGaps.push({
      specifier: null,
      reason: 'cross_module_resolution_incomplete',
      source: { path: null, block: null },
      production_reachable: true,
    })
  }
  if (requestedEntries.length === 0) {
    reachabilityGaps.push({
      specifier: null,
      reason: 'production_entry_missing',
      source: { path: null, block: null },
      production_reachable: true,
    })
  }

  const dedupedEntities = [...new Map(usageEntities.map((entity) => [entity.id, entity])).values()]
    .sort((left, right) => {
      const byPath = left.source.path.localeCompare(right.source.path)
      return byPath || left.source.line - right.source.line || left.source.column - right.source.column
    })
  const payload = {
    schema_version: 1,
    generated_at: new Date().toISOString(),
    project_root: projectRoot,
    entries: requestedEntries.map((entry) => toPosix(path.relative(projectRoot, entry))),
    incremental: {
      enabled: Boolean(changedFiles),
      changed_files: changedFiles ? [...changedFiles].map((file) => toPosix(path.relative(projectRoot, file))).sort() : [],
      analyzed_files: incrementalFiles ? [...incrementalFiles].map((file) => toPosix(path.relative(projectRoot, file))).sort() : [],
      complete_surface: !changedFiles,
      restriction: changedFiles
        ? 'Delta output is review metadata only; run a full extraction before Contract CI.'
        : null,
    },
    resolver: {
      primary: 'ast',
      javascript_typescript: '@babel/parser',
      vue_sfc: '@vue/compiler-sfc -> @babel/parser',
      symbol_mode: 'bounded cross-module alias/re-export and constructor-instance resolution',
      module_flow_converged: moduleFlowConverged,
      contract_return_types: args.contract ? 'structured reference/Promise<reference> only' : 'disabled',
      alias_config: args.aliasConfig ? 'explicit JSON profile' : 'built-in @/ and ~/',
      production_reachability: 'static module import graph',
      regex_role: 'discovery_fallback_only',
    },
    reachable_files: [...reachable].map((file) => toPosix(path.relative(projectRoot, file))).sort(),
    usage_entities: dedupedEntities,
    parse_failures: parseFailures,
    reachability_gaps: reachabilityGaps,
    discovery_findings: discoveryFindings,
    summary: {
      source_files: files.length,
      reachable_files: reachable.size,
      usage_entities: dedupedEntities.length,
      resolved: dedupedEntities.filter((entity) => entity.resolution_status === 'resolved').length,
      ambiguous: dedupedEntities.filter((entity) => entity.resolution_status === 'ambiguous').length,
      dynamic_unresolved: dedupedEntities.filter((entity) => entity.resolution_status === 'dynamic_unresolved').length,
      parse_failed: parseFailures.length,
      reachability_gaps: reachabilityGaps.length,
      regex_discoveries: discoveryFindings.length,
    },
    limitations: [
      'Cross-module propagation is limited to statically imported/exported namespace or instance references and bounded re-export chains.',
      'Lexical path sensitivity is conservative; conflicting aliases across scopes become ambiguous.',
      'Factory functions, callback returns, dynamic imports and unresolved cycles are not treated as ThingJS aliases.',
      'Static reachability supports relative, root, @/, and ~/ imports; unresolved production imports block validation.',
      'Nested instance paths require schema-3 structured Contract return-type information; unknown or legacy returns remain unresolved.',
      'Incremental output is a changed-file delta and cannot replace a complete Usage Surface in Contract CI.',
      'Regex findings are never verified Usage Entities.',
    ],
    cache: {
      enabled: Boolean(cachePath),
      hit: false,
      invalidated_files: [...cacheInvalidatedFiles].sort(),
      reused_files: [],
      reason: cachePath
        ? (changedFiles ? 'explicit_changed_files' : cacheResult.reason || 'content_changed')
        : null,
    },
  }

  const output = path.resolve(args.output)
  fs.mkdirSync(path.dirname(output), { recursive: true })
  fs.writeFileSync(output, JSON.stringify(payload, null, 2) + '\n', 'utf8')
  writeResolverCache(cachePath, projectRoot, configurationSignature, fileHashes, payload)
  process.stdout.write(`${JSON.stringify(payload.summary, null, 2)}\n`)
  return 0
}

try {
  process.exitCode = main()
} catch (error) {
  process.stderr.write(`${error.stack || error}\n`)
  process.exitCode = 1
}
