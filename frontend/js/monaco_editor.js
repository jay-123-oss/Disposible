/**
 * Monaco Editor Integration Module for Antigravity IDE
 */

window.AntigravityEditor = (function () {
  let editorInstance = null;
  let currentFilePath = null;
  let isDirty = false;

  const getLanguage = (pathStr) => {
    if (!pathStr) return 'plaintext';
    const ext = pathStr.split('.').pop().toLowerCase();
    switch (ext) {
      case 'js':
      case 'jsx':
        return 'javascript';
      case 'ts':
      case 'tsx':
        return 'typescript';
      case 'html':
      case 'htm':
        return 'html';
      case 'css':
        return 'css';
      case 'json':
        return 'json';
      case 'py':
        return 'python';
      case 'rs':
        return 'rust';
      case 'go':
        return 'go';
      case 'md':
        return 'markdown';
      case 'yml':
      case 'yaml':
        return 'yaml';
      case 'sh':
      case 'bat':
        return 'shell';
      default:
        return 'plaintext';
    }
  };

  function init(containerId, onCursorChange, onSave) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (window.require) {
      window.require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs' } });
      window.require(['vs/editor/editor.main'], function () {
        editorInstance = monaco.editor.create(container, {
          value: '// Welcome to Antigravity IDE\n// Select a file from the explorer or prompt the 6-Agent Swarm.\n',
          language: 'javascript',
          theme: 'vs-dark',
          automaticLayout: true,
          minimap: { enabled: true },
          fontSize: 13,
          fontFamily: "'JetBrains Mono', Consolas, monospace",
          lineNumbers: 'on',
          renderLineHighlight: 'all',
          tabSize: 2,
        });

        editorInstance.onDidChangeCursorPosition((e) => {
          if (onCursorChange) {
            onCursorChange(e.position.lineNumber, e.position.column);
          }
        });

        editorInstance.onDidChangeModelContent(() => {
          isDirty = true;
        });

        // Add Ctrl+S action
        editorInstance.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
          if (onSave && currentFilePath) {
            onSave(currentFilePath, editorInstance.getValue());
            isDirty = false;
          }
        });
      });
    } else {
      // Fallback
      container.innerHTML = '<textarea id="fallback-editor" style="width:100%;height:100%;background:#0d1117;color:#f0f6fc;font-family:monospace;padding:12px;border:none;outline:none;resize:none;"></textarea>';
    }
  }

  function openFile(path, content) {
    currentFilePath = path;
    const lang = getLanguage(path);

    if (editorInstance && window.monaco) {
      const oldModel = editorInstance.getModel();
      const newModel = monaco.editor.createModel(content, lang);
      editorInstance.setModel(newModel);
      if (oldModel) oldModel.dispose();
      isDirty = false;
    } else {
      const fallback = document.getElementById('fallback-editor');
      if (fallback) fallback.value = content;
    }
  }

  function getValue() {
    if (editorInstance) return editorInstance.getValue();
    const fallback = document.getElementById('fallback-editor');
    return fallback ? fallback.value : '';
  }

  function getCurrentPath() {
    return currentFilePath;
  }

  return {
    init,
    openFile,
    getValue,
    getCurrentPath,
  };
})();
