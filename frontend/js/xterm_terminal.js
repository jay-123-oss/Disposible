/**
 * Terminal Subsystem for Antigravity IDE
 */

window.AntigravityTerminal = (function () {
  let terminalElement = null;

  function init(elementId) {
    terminalElement = document.getElementById(elementId);
  }

  function appendLine(text, type = 'info') {
    if (!terminalElement) return;
    const line = document.createElement('div');
    line.className = `term-line ${type}`;
    line.textContent = text;
    terminalElement.appendChild(line);
    terminalElement.scrollTop = terminalElement.scrollHeight;
  }

  function clear() {
    if (!terminalElement) return;
    terminalElement.innerHTML = '<div class="term-line info">[Terminal cleared]</div>';
  }

  return {
    init,
    appendLine,
    clear,
  };
})();
