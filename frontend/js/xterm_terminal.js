/**
 * Terminal Subsystem for Antigravity IDE
 *
 * Keeps an in-memory log buffer so the Output and Debug Console tabs can
 * render filtered views of everything the agents and tools have printed.
 */

window.AntigravityTerminal = (function () {
  let terminalElement = null;
  let buffer = [];       // { text, type }
  let view = 'terminal'; // 'terminal' | 'output' | 'debug'

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function render() {
    if (!terminalElement) return;
    if (view === 'terminal') {
      terminalElement.innerHTML = buffer
        .map((l) => `<div class="term-line ${l.type}">${escapeHtml(l.text)}</div>`)
        .join('');
    } else {
      const filtered = view === 'debug'
        ? buffer.filter((l) => /error|fail|exception|traceback|warning/i.test(l.text))
        : buffer;
      terminalElement.innerHTML = filtered.length
        ? filtered.map((l) => `<div class="term-line ${l.type}">${escapeHtml(l.text)}</div>`).join('')
        : `<div class="term-view-empty">${
            view === 'debug'
              ? 'No errors or warnings logged yet.'
              : 'No output yet. Run a task or a debug target to see output here.'
          }</div>`;
    }
    terminalElement.scrollTop = terminalElement.scrollHeight;
  }

  function init(elementId) {
    terminalElement = document.getElementById(elementId);
    if (!terminalElement) return;
    // Seed the buffer from the static welcome lines in the HTML.
    buffer = [];
    terminalElement.querySelectorAll('.term-line').forEach((el) => {
      buffer.push({ text: el.textContent, type: el.className.replace('term-line', '').trim() || 'info' });
    });
    render();
  }

  function appendLine(text, type = 'info') {
    buffer.push({ text: String(text), type: type });
    render();
  }

  function clear() {
    buffer = [];
    appendLine('Terminal cleared', 'info');
  }

  function setView(nextView) {
    if (!['terminal', 'output', 'debug'].includes(nextView)) return;
    view = nextView;
    render();
  }

  function getView() {
    return view;
  }

  return {
    init,
    appendLine,
    clear,
    setView,
    getView,
  };
})();