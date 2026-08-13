/*
 * 在真实浏览器中读取 ThingJS 的公开运行时表面。
 *
 * 该探针只读取 property descriptor，不调用构造器或 getter，因此它只能证明
 * owner/member 在已加载制品中存在，不能证明参数、返回值或生命周期行为。
 */
(function exposeRuntimeSurfaceProbe(root, factory) {
  const collectRuntimeSurface = factory()
  if (typeof module === 'object' && module.exports) {
    module.exports = collectRuntimeSurface
  }
  root.__THINGJS_COLLECT_RUNTIME_SURFACE__ = collectRuntimeSurface
})(typeof globalThis === 'object' ? globalThis : window, function createProbe() {
  'use strict'

  const DEFAULT_MAX_NAMESPACE_DEPTH = 2
  const IGNORED_MEMBER_NAMES = new Set([
    'arguments',
    'caller',
    'length',
    'name',
    'prototype',
  ])

  function isPublicName(name) {
    return typeof name === 'string' && name.length > 0 && !name.startsWith('_')
  }

  function valueKind(value) {
    if (value === null) return 'null'
    if (Array.isArray(value)) return 'array'
    return typeof value
  }

  function descriptorKind(descriptor) {
    if (typeof descriptor.value === 'function') return 'method'
    if (descriptor.get || descriptor.set) return 'accessor'
    return 'property'
  }

  function selectCanonicalPath(paths) {
    if (!paths || paths.length === 0) return null
    return [...paths].sort((left, right) => {
      const depthDifference = left.split('.').length - right.split('.').length
      return depthDifference || left.localeCompare(right)
    })[0]
  }

  /**
   * 收集命名空间、构造器和 prototype 成员，并保留继承声明位置。
   * @param {object} options 探针参数；`rootName` 默认为 `THING`。
   * @returns {object} 可序列化的 Runtime Surface，不含函数值或业务数据。
   */
  function collectRuntimeSurface(options = {}) {
    const rootName = options.rootName || 'THING'
    const maxNamespaceDepth = Number.isInteger(options.maxNamespaceDepth)
      ? options.maxNamespaceDepth
      : DEFAULT_MAX_NAMESPACE_DEPTH
    const rootDescriptor = Object.getOwnPropertyDescriptor(globalThis, rootName)
    const runtimeRoot = rootDescriptor && Object.prototype.hasOwnProperty.call(rootDescriptor, 'value')
      ? rootDescriptor.value
      : undefined

    if (!runtimeRoot || (typeof runtimeRoot !== 'object' && typeof runtimeRoot !== 'function')) {
      throw new Error(`Global runtime root ${rootName} is unavailable.`)
    }

    const objectPaths = new Map()
    const namespaceQueue = [{
      path: rootName,
      value: runtimeRoot,
      depth: 0,
      containerKind: 'namespace',
    }]
    const visited = new Set()
    const namespaceMembers = []
    const constructors = []
    const constructorValues = new Map()

    while (namespaceQueue.length > 0) {
      const current = namespaceQueue.shift()
      if (visited.has(current.value)) continue
      visited.add(current.value)

      const knownPaths = objectPaths.get(current.value) || []
      knownPaths.push(current.path)
      objectPaths.set(current.value, knownPaths)

      let descriptors
      try {
        descriptors = Object.getOwnPropertyDescriptors(current.value)
      } catch (error) {
        continue
      }

      for (const [name, descriptor] of Object.entries(descriptors)) {
        if (!isPublicName(name) || IGNORED_MEMBER_NAMES.has(name)) continue
        const memberPath = `${current.path}.${name}`
        const memberValue = Object.prototype.hasOwnProperty.call(descriptor, 'value')
          ? descriptor.value
          : undefined
        const member = {
          owner: current.path,
          member: name,
          runtime_path: memberPath,
          kind: descriptorKind(descriptor),
          value_kind: valueKind(memberValue),
          readable: Boolean(descriptor.get) || Object.prototype.hasOwnProperty.call(descriptor, 'value'),
          writable: Boolean(descriptor.set) || descriptor.writable === true,
        }
        namespaceMembers.push(member)

        if (current.containerKind === 'namespace' && typeof memberValue === 'function') {
          constructors.push({
            owner: memberPath,
            member: 'constructor',
            runtime_path: memberPath,
            kind: 'constructor',
            proves: 'function_valued_owner_exists',
          })
          constructorValues.set(memberPath, memberValue)
        }

        if (
          current.containerKind === 'namespace' &&
          current.depth < maxNamespaceDepth &&
          memberValue &&
          (typeof memberValue === 'object' || typeof memberValue === 'function')
        ) {
          const childPaths = objectPaths.get(memberValue) || []
          childPaths.push(memberPath)
          objectPaths.set(memberValue, childPaths)
          namespaceQueue.push({
            path: memberPath,
            value: memberValue,
            depth: current.depth + 1,
            // 类只展开一层静态成员；静态方法不是新的公开构造器或命名空间。
            containerKind: typeof memberValue === 'function' ? 'class' : 'namespace',
          })
        }
      }
    }

    const prototypeMembers = []
    const inheritance = []
    for (const constructorRecord of constructors) {
      const constructorValue = constructorValues.get(constructorRecord.owner)
      if (typeof constructorValue !== 'function' || !constructorValue.prototype) continue

      const prototype = constructorValue.prototype
      let descriptors
      try {
        descriptors = Object.getOwnPropertyDescriptors(prototype)
      } catch (error) {
        continue
      }
      for (const [name, descriptor] of Object.entries(descriptors)) {
        if (name === 'constructor' || !isPublicName(name)) continue
        prototypeMembers.push({
          effective_owner: constructorRecord.owner,
          declared_owner: constructorRecord.owner,
          member: name,
          runtime_path: `${constructorRecord.owner}.prototype.${name}`,
          kind: descriptorKind(descriptor),
          inherited: false,
          readable: Boolean(descriptor.get) || Object.prototype.hasOwnProperty.call(descriptor, 'value'),
          writable: Boolean(descriptor.set) || descriptor.writable === true,
        })
      }

      // 继承关系单独记录；成员不在每个子类上重复展开，避免 Surface 随类数平方膨胀。
      const parentPrototype = Object.getPrototypeOf(prototype)
      const parentConstructor = parentPrototype
        ? Object.getOwnPropertyDescriptor(parentPrototype, 'constructor')?.value
        : null
      const parentPaths = parentConstructor ? objectPaths.get(parentConstructor) : null
      const parentOwner = selectCanonicalPath(parentPaths)
      if (parentOwner && parentOwner !== constructorRecord.owner) {
        inheritance.push({ child: constructorRecord.owner, parent: parentOwner })
      }
    }

    const dedupe = (records, keyOf) => {
      const byKey = new Map()
      for (const record of records) byKey.set(keyOf(record), record)
      return [...byKey.values()].sort((left, right) => keyOf(left).localeCompare(keyOf(right)))
    }

    const versionDescriptor = Object.getOwnPropertyDescriptor(runtimeRoot, 'VERSION')
    const runtimeVersion = versionDescriptor && typeof versionDescriptor.value === 'string'
      ? versionDescriptor.value
      : null

    return {
      schema_version: 1,
      captured_at: new Date().toISOString(),
      runtime_root: rootName,
      runtime_version: runtimeVersion,
      constructors: dedupe(constructors, (record) => record.owner),
      namespace_members: dedupe(
        namespaceMembers,
        (record) => `${record.owner}|${record.member}|${record.kind}`,
      ),
      prototype_members: dedupe(
        prototypeMembers,
        (record) => `${record.effective_owner}|${record.declared_owner}|${record.member}|${record.kind}`,
      ),
      inheritance: dedupe(inheritance, (record) => `${record.child}|${record.parent}`),
      limitations: [
        'Descriptor inspection proves member existence only.',
        'No constructor, getter, method, scene, lifecycle, or rendering behavior was executed.',
      ],
    }
  }

  return collectRuntimeSurface
})
