// Custom plugin to handle @babel/runtime/helpers/esm imports
export default function babelRuntimePlugin() {
  const virtualModuleId = '@babel/runtime/helpers/esm/';
  const resolvedVirtualModuleId = '\0' + virtualModuleId;

  return {
    name: 'vite-plugin-babel-runtime',
    resolveId(id) {
      if (id.startsWith('@babel/runtime/helpers/esm/')) {
        // Convert esm path to regular path
        const helperName = id.replace('@babel/runtime/helpers/esm/', '');
        return { id: `\0virtual:babel-runtime/${helperName}`, external: false };
      }
      return null;
    },
    load(id) {
      if (id.startsWith('\0virtual:babel-runtime/')) {
        const helperName = id.replace('\0virtual:babel-runtime/', '');
        
        // Provide implementation for common Babel helpers
        if (helperName === 'extends') {
          return `
export default function _extends() {
  _extends = Object.assign ? Object.assign.bind() : function (target) {
    for (var i = 1; i < arguments.length; i++) {
      var source = arguments[i];
      for (var key in source) {
        if (Object.prototype.hasOwnProperty.call(source, key)) {
          target[key] = source[key];
        }
      }
    }
    return target;
  };
  return _extends.apply(this, arguments);
}`;
        }
        
        if (helperName === 'objectWithoutPropertiesLoose') {
          return `
export default function _objectWithoutPropertiesLoose(source, excluded) {
  if (source == null) return {};
  var target = {};
  var sourceKeys = Object.keys(source);
  var key, i;
  for (i = 0; i < sourceKeys.length; i++) {
    key = sourceKeys[i];
    if (excluded.indexOf(key) >= 0) continue;
    target[key] = source[key];
  }
  return target;
}`;
        }
        
        if (helperName === 'inheritsLoose') {
          return `
export default function _inheritsLoose(subClass, superClass) {
  subClass.prototype = Object.create(superClass.prototype);
  subClass.prototype.constructor = subClass;
  subClass.__proto__ = superClass;
}`;
        }
        
        if (helperName === 'assertThisInitialized') {
          return `
export default function _assertThisInitialized(self) {
  if (self === void 0) {
    throw new ReferenceError("this hasn't been initialised - super() hasn't been called");
  }
  return self;
}`;
        }
        
        // Default case for other helpers
        return `export default function ${helperName}() { 
  console.warn('${helperName} is not fully implemented'); 
  return {}; 
}`;
      }
      return null;
    }
  };
}
