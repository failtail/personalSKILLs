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
  return base.type === 'dynamic' ? base : null
}

function collectBindings(ast, constants, contractIndex) {
  const bindings = new Map()
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

function analyzeSegment(filename, relativePath, segment, contractIndex) {
  const constants = collectConstants(segment.ast)
  const bindings = collectBindings(segment.ast, constants, contractIndex)
  const entities = []
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
    if (
      node.type === 'CallExpression' &&
      node.callee?.type === 'Import' &&
      node.arguments.length === 1
    ) {
      const value = evaluateStaticString(node.arguments[0], constants)
      if (value !== null) imports.push(value)
      else recordDynamicImportGap(node, 'dynamic_import_specifier')
    }
    if (
      node.type === 'CallExpression' &&
      node.callee?.type === 'Identifier' &&
      node.callee.name === 'require' &&
      node.arguments.length === 1
    ) {
      const value = evaluateStaticString(node.arguments[0], constants)
      if (value !== null) imports.push(value)
      else recordDynamicImportGap(node, 'dynamic_require_specifier')
    }

    const isMember = node.type === 'MemberExpression' || node.type === 'OptionalMemberExpression'
    if (isMember) {
      if (isNestedMemberObject(node, parent)) return
      const reference = resolveReference(node, bindings, constants, contractIndex)
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
      if (reference?.type !== 'namespace') return
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
  const requestedEntries = args.entries.length > 0
    ? args.entries.map((entry) => path.resolve(projectRoot, entry))
    : defaultEntries(projectRoot)
  const importGraph = new Map(files.map((file) => [path.normalize(file), []]))
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

    const coveredTokens = new Set()
    for (const segment of segments) {
      const analysis = analyzeSegment(filename, relativePath, segment, contractIndex)
      usageEntities.push(...analysis.entities)
      for (const entity of analysis.entities) {
        for (const token of entity.expression.match(THING_TOKEN_PATTERN) || []) coveredTokens.add(token)
      }
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

    for (const finding of regexDiscoveries(relativePath, source, 'unmodeled_pattern')) {
      if (!coveredTokens.has(finding.token)) discoveryFindings.push(finding)
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
    resolver: {
      primary: 'ast',
      javascript_typescript: '@babel/parser',
      vue_sfc: '@vue/compiler-sfc -> @babel/parser',
      symbol_mode: 'file-scope alias/destructuring and constructor-instance resolution',
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
      'Cross-module value flow and runtime call graphs are not inferred.',
      'Lexical path sensitivity is conservative; conflicting aliases across scopes become ambiguous.',
      'Imported values are not treated as ThingJS aliases without local provenance.',
      'Static reachability supports relative, root, @/, and ~/ imports; unresolved production imports block validation.',
      'Nested instance paths require schema-3 structured Contract return-type information; unknown or legacy returns remain unresolved.',
      'Regex findings are never verified Usage Entities.',
    ],
  }

  const output = path.resolve(args.output)
  fs.mkdirSync(path.dirname(output), { recursive: true })
  fs.writeFileSync(output, `${JSON.stringify(payload, null, 2)}\n`, 'utf8')
  process.stdout.write(`${JSON.stringify(payload.summary, null, 2)}\n`)
  return 0
}

try {
  process.exitCode = main()
} catch (error) {
  process.stderr.write(`${error.stack || error}\n`)
  process.exitCode = 1
}
