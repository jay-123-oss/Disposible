/**
 * Main Application Coordinator for Antigravity IDE
 *
 * Wires every visible button/panel in the shell:
 *  - Activity bar panel switching (Explorer / Search / SCM / Run&Debug / Extensions)
 *  - Top menu bar dropdowns (File, Edit, Selection, View, Go, Run, Terminal, Help)
 *  - Terminal drawer (clear, size toggle, Terminal / Output / Debug Console tabs)
 *  - Live preview tab toggle
 *  - Explorer tree, editor tabs, and file save flows
 */

window.AntigravityApp = (function () {
  let activeFilePath = null;
  let openMenuTrigger = null; // menu trigger whose dropdown is currently open

  // -------------------------------------------------------------------------
  // Panel state
  // -------------------------------------------------------------------------
  const ACTIVITY_PANELS = {
    'act-explorer': 'explorer-panel',
    'act-search': 'search-panel',
    'act-scm': 'scm-panel',
    'act-debug': 'debug-panel',
    'act-extensions': 'extensions-panel',
  };

  function init() {
    // 1. Initialize Subsystems
    AntigravityTerminal.init('terminal-output');
    AntigravityChat.init();

    AntigravityEditor.init(
      'monaco-container',
      (line, col) => {
        const coords = document.getElementById('editor-coords');
        if (coords) coords.textContent = `Ln ${line}, Col ${col}`;
      },
      (path, content) => {
        saveFile(path, content);
      }
    );

    // 2. Load File Explorer
    refreshFiles();

    // 3. Bind UI Handlers
    bindHeaderActions();
    bindExplorerActions();
    bindLivePreview();
    bindActivityBar();
    bindMenus();
    bindTerminalTabs();
    bindPreviewTab();
    bindSearchPanel();
    bindScmPanel();
    initExtensions();

    // 4. Initial Live Preview if index.html exists
    setTimeout(() => {
      refreshPreview();
    }, 1000);
  }

  // -------------------------------------------------------------------------
  // Activity Bar
  // -------------------------------------------------------------------------
  function bindActivityBar() {
    Object.keys(ACTIVITY_PANELS).forEach((btnId) => {
      const btn = document.getElementById(btnId);
      if (!btn) return;
      btn.addEventListener('click', () => toggleSidePanel(btnId));
    });
  }

  function toggleSidePanel(btnId) {
    const panelId = ACTIVITY_PANELS[btnId];
    const btn = document.getElementById(btnId);
    const panel = document.getElementById(panelId);
    if (!panel) return;

    const isAlreadyActive = btn.classList.contains('active');
    // Hide everything first
    document.querySelectorAll('.side-panel').forEach((p) => p.classList.remove('visible'));
    document.querySelectorAll('.activity-bar .act-btn').forEach((b) => b.classList.remove('active'));

    if (!isAlreadyActive) {
      panel.classList.add('visible');
      btn.classList.add('active');
      // Refresh panel content when it becomes visible
      if (panelId === 'scm-panel') loadScmStatus();
      if (panelId === 'debug-panel') loadDebugTargets();
      if (panelId === 'search-panel') {
        const input = document.getElementById('search-input');
        if (input) input.focus();
      }
    }
  }

  function openSidePanel(btnId) {
    const btn = document.getElementById(btnId);
    if (btn && !btn.classList.contains('active')) toggleSidePanel(btnId);
  }

  // -------------------------------------------------------------------------
  // Top Menu Bar
  // -------------------------------------------------------------------------
  const MENUS = {
    file: [
      { label: 'New File', action: () => { const fname = prompt('Enter new file name:'); if (fname) saveFile(fname, '').then(() => { refreshFiles(); loadFile(fname); }); } },
      { label: 'New Folder', action: () => { const folderName = prompt('Enter new folder name:'); if (folderName) saveFile(`${folderName}/.gitkeep`, '').then(() => refreshFiles()); } },
      { type: 'sep' },
      { label: 'Save File', kbd: 'Ctrl+S', action: saveCurrentFile },
      { label: 'Refresh Explorer', action: refreshFiles },
    ],
    edit: [
      { label: 'Undo', kbd: 'Ctrl+Z', action: () => AntigravityEditor.undo() },
      { label: 'Redo', kbd: 'Ctrl+Y', action: () => AntigravityEditor.redo() },
    ],
    selection: [
      { label: 'Select All', kbd: 'Ctrl+A', action: () => AntigravityEditor.selectAll() },
    ],
    view: [
      { label: 'Toggle Explorer', action: () => toggleSidePanel('act-explorer') },
      { label: 'Toggle Terminal', action: toggleTerminal },
      { label: 'Toggle Live Preview', action: togglePreview },
    ],
    go: [
      { label: 'Go to Line…', kbd: 'Ctrl+G', action: goToLinePrompt },
    ],
    run: [
      { label: 'Deploy to GPU', action: triggerDeploy },
      { type: 'sep' },
      { label: 'Run Smoke Tests', action: () => { openSidePanel('act-debug'); runDebugTarget('smoke'); } },
      { label: 'Run Full Test Suite', action: () => { openSidePanel('act-debug'); runDebugTarget('pytest'); } },
    ],
    terminal: [
      { label: 'Clear Terminal', action: () => AntigravityTerminal.clear() },
      { label: 'Toggle Terminal Size', action: toggleTerminalSize },
      { label: 'Show / Hide Terminal', action: toggleTerminal },
    ],
    help: [
      { label: 'About Antigravity IDE', action: showAbout },
    ],
  };

  function bindMenus() {
    const dropdown = document.getElementById('menu-dropdown');
    const triggers = document.querySelectorAll('.menu-trigger[data-menu]');

    triggers.forEach((trigger) => {
      trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        if (openMenuTrigger === trigger && !dropdown.classList.contains('hidden')) {
          hideDropdown();
          return;
        }
        const menuName = trigger.dataset.menu;
        const items = MENUS[menuName];
        if (!items) return;
        renderDropdown(items, trigger);
        openMenuTrigger = trigger;
      });
    });

    // Close on outside click / Escape
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.menu-trigger')) hideDropdown();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') hideDropdown();
    });
  }

  function hideDropdown() {
    openMenuTrigger = null;
    const dropdown = document.getElementById('menu-dropdown');
    if (dropdown) dropdown.classList.add('hidden');
  }

  function renderDropdown(items, anchor) {
    const dropdown = document.getElementById('menu-dropdown');
    if (!dropdown) return;
    dropdown.innerHTML = '';

    items.forEach((item) => {
      if (item.type === 'sep') {
        const sep = document.createElement('div');
        sep.className = 'menu-dropdown-sep';
        dropdown.appendChild(sep);
        return;
      }
      const row = document.createElement('div');
      row.className = 'menu-dropdown-item';
      row.innerHTML = `<span>${item.label}</span>${item.kbd ? `<span class="menu-dropdown-kbd">${item.kbd}</span>` : ''}`;
      row.addEventListener('click', (e) => {
        e.stopPropagation();
        hideDropdown();
        try {
          item.action();
        } catch (err) {
          AntigravityTerminal.appendLine(`[Menu Error] ${err.message}`, 'info');
        }
      });
      dropdown.appendChild(row);
    });

    const rect = anchor.getBoundingClientRect();
    dropdown.style.left = `${rect.left}px`;
    dropdown.style.top = `${rect.bottom + 4}px`;
    dropdown.classList.remove('hidden');
  }

  function saveCurrentFile() {
    const path = AntigravityEditor.getCurrentPath();
    if (!path) {
      AntigravityTerminal.appendLine('[Save] No file is open in the editor.', 'info');
      return;
    }
    saveFile(path, AntigravityEditor.getValue());
  }

  function goToLinePrompt() {
    if (!AntigravityEditor.isReady()) {
      AntigravityTerminal.appendLine('[Go] Editor not ready yet.', 'info');
      return;
    }
    const line = prompt('Go to line:');
    if (line) AntigravityEditor.goToLine(parseInt(line, 10) || 1);
  }

  function showAbout() {
    fetch('/api/status')
      .then((r) => r.json())
      .then((st) => {
        const lines = [
          'Antigravity+ IDE — 6-Agent Swarm Browser Edition',
          `Version: ${st.ide_version || 'n/a'} | Theme: ${st.theme || 'n/a'}`,
          `LLM backend: ${st.llm ? st.llm.provider + ' (' + st.llm.mode + ')' : 'n/a'}`,
          'Features: File explorer, Monaco editor, live preview, terminal, agent chat, model settings, search, source control, run & debug, extensions.',
        ];
        lines.forEach((l) => AntigravityTerminal.appendLine(l, 'success'));
      })
      .catch(() => AntigravityTerminal.appendLine('Antigravity+ IDE — About: could not reach /api/status.', 'info'));
  }

  // -------------------------------------------------------------------------
  // Terminal Drawer
  // -------------------------------------------------------------------------
  function toggleTerminal() {
    const drawer = document.getElementById('terminal-drawer');
    if (!drawer) return;
    drawer.classList.toggle('hidden');
  }

  function toggleTerminalSize() {
    const drawer = document.getElementById('terminal-drawer');
    if (!drawer) return;
    drawer.classList.toggle('compact');
  }

  function bindTerminalTabs() {
    const tabsContainer = document.getElementById('terminal-tabs');
    if (!tabsContainer) return;
    tabsContainer.querySelectorAll('.term-tab').forEach((tab) => {
      tab.addEventListener('click', () => {
        tabsContainer.querySelectorAll('.term-tab').forEach((t) => t.classList.remove('active'));
        tab.classList.add('active');
        AntigravityTerminal.setView(tab.dataset.termTab);
      });
    });

    const sizeBtn = document.getElementById('btn-toggle-term');
    if (sizeBtn) sizeBtn.addEventListener('click', toggleTerminalSize);
  }

  // -------------------------------------------------------------------------
  // Live Preview Tab (editor tabs bar)
  // -------------------------------------------------------------------------
  function togglePreview() {
    const preview = document.getElementById('preview-container');
    const monaco = document.getElementById('monaco-container');
    const tab = document.getElementById('tab-preview');
    if (!preview) return;
    const hidden = preview.classList.toggle('hidden');
    if (monaco) monaco.classList.toggle('full', hidden);
    if (tab) tab.classList.toggle('active', !hidden);
  }

  function bindPreviewTab() {
    const tab = document.getElementById('tab-preview');
    if (tab) tab.addEventListener('click', togglePreview);
  }

  // -------------------------------------------------------------------------
  // Search Panel
  // -------------------------------------------------------------------------
  function bindSearchPanel() {
    const input = document.getElementById('search-input');
    const btn = document.getElementById('btn-run-search');
    if (!input || !btn) return;

    const run = () => {
      const q = input.value.trim();
      if (!q) return;
      runSearch(q);
    };
    btn.addEventListener('click', run);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') run();
    });
  }

  function runSearch(q) {
    const container = document.getElementById('search-results');
    if (!container) return;
    container.innerHTML = '<div class="empty-tree-hint">Searching…</div>';

    fetch(`/api/search?q=${encodeURIComponent(q)}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status !== 'success') {
          container.innerHTML = `<div class="empty-tree-hint">${data.detail || 'Search failed.'}</div>`;
          return;
        }
        container.innerHTML = '';
        if (!data.results.length) {
          container.innerHTML = `<div class="empty-tree-hint">No results for “${q}”.</div>`;
          return;
        }
        data.results.forEach((r) => {
          const row = document.createElement('div');
          row.className = 'search-result-item';
          const match = r.matches && r.matches[0];
          const line = match ? match.line : null;
          const pathHtml = highlight(r.path, q);
          const snippetHtml = match ? highlight(match.snippet, q) : '<span class="search-result-line">filename match</span>';
          row.innerHTML = `
            <div class="search-result-path">${pathHtml}</div>
            ${line ? `<div class="search-result-line">${line}: ${snippetHtml}</div>` : snippetHtml}
          `;
          row.addEventListener('click', () => {
            AntigravityApp.loadFile(r.path).then(() => {
              if (line) AntigravityEditor.goToLine(line);
            });
          });
          container.appendChild(row);
        });
      })
      .catch((err) => {
        container.innerHTML = `<div class="empty-tree-hint">Error: ${err.message}</div>`;
      });
  }

  function highlight(text, q) {
    const escaped = String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const needle = String(q).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return escaped.replace(new RegExp(`(${needle})`, 'ig'), '<b>$1</b>');
  }

  // -------------------------------------------------------------------------
  // Source Control Panel
  // -------------------------------------------------------------------------
  function bindScmPanel() {
    const btn = document.getElementById('btn-refresh-scm');
    if (btn) btn.addEventListener('click', loadScmStatus);
  }

  function loadScmStatus() {
    const branchEl = document.getElementById('scm-branch');
    const changesEl = document.getElementById('scm-changes');
    const commitsEl = document.getElementById('scm-commits-list');
    if (!branchEl || !changesEl) return;

    branchEl.textContent = 'Loading…';
    changesEl.innerHTML = '';
    if (commitsEl) commitsEl.innerHTML = '';

    fetch('/api/git/status')
      .then((res) => res.json())
      .then((data) => {
        if (data.status !== 'success') {
          branchEl.textContent = '⚠ Not a git repository';
          changesEl.innerHTML = `<div class="scm-empty">${data.message || 'No git data available.'}</div>`;
          return;
        }
        branchEl.textContent = `⑂ ${data.branch}`;
        if (!data.changes.length) {
          changesEl.innerHTML = '<div class="scm-empty">Working tree clean.</div>';
        } else {
          data.changes.forEach((c) => {
            const row = document.createElement('div');
            row.className = 'scm-change-item';
            let codeClass = 'mod';
            if (c.code.includes('?')) codeClass = 'untracked';
            else if (c.code.includes('A')) codeClass = 'add';
            else if (c.code.includes('D')) codeClass = 'del';
            row.innerHTML = `<span class="scm-change-code ${codeClass}">${c.code}</span><span class="scm-change-path">${c.path}</span>`;
            row.addEventListener('click', () => {
              // Strip rename arrows ("a -> b") by taking the last path
              const target = c.path.split(' -> ').pop().trim();
              if (target) AntigravityApp.loadFile(target);
            });
            changesEl.appendChild(row);
          });
        }
        if (commitsEl) {
          if (!data.commits.length) {
            commitsEl.innerHTML = '<div class="scm-empty">No commits yet.</div>';
          } else {
            data.commits.forEach((c) => {
              const item = document.createElement('div');
              item.className = 'scm-commit-item';
              item.textContent = c;
              commitsEl.appendChild(item);
            });
          }
        }
      })
      .catch((err) => {
        branchEl.textContent = '⚠ Error';
        changesEl.innerHTML = `<div class="scm-empty">${err.message}</div>`;
      });
  }

  // -------------------------------------------------------------------------
  // Run & Debug Panel
  // Targets are bound where they render: loadDebugTargets() attaches the Run
  // click handler to each row, and runDebugTarget() drives the POST. No init
  // stub needed.
  function loadDebugTargets() {
    const list = document.getElementById('debug-target-list');
    if (!list) return;
    list.innerHTML = '<div class="empty-tree-hint">Loading targets…</div>';

    fetch('/api/debug/targets')
      .then((res) => res.json())
      .then((data) => {
        list.innerHTML = '';
        (data.targets || []).forEach((t) => {
          const row = document.createElement('div');
          row.className = 'debug-target-item';
          const btn = document.createElement('button');
          btn.textContent = 'Run';
          btn.addEventListener('click', () => runDebugTarget(t.id, btn));
          row.innerHTML = `<span>${t.label}</span>`;
          row.appendChild(btn);
          list.appendChild(row);
        });
      })
      .catch((err) => {
        list.innerHTML = `<div class="empty-tree-hint">Error: ${err.message}</div>`;
      });
  }

  function runDebugTarget(targetId, button) {
    const resultEl = document.getElementById('debug-result');
    const label = targetId === 'pytest' ? 'Full Test Suite' : targetId === 'smoke' ? 'Smoke Tests' : 'Compile Check';
    if (!resultEl) return;

    if (button) {
      button.disabled = true;
      button.textContent = 'Running…';
    }
    resultEl.innerHTML = `<span class="ok">▶ Running ${label}… this can take a while.</span>`;
    AntigravityTerminal.appendLine(`[Debug] Running ${label} (${targetId})…`, 'info');

    fetch('/api/debug/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target: targetId }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'success') {
          resultEl.innerHTML = `<span class="ok">✓ ${label} passed in ${data.elapsed_seconds}s (exit ${data.exit_code}).</span>\n${data.output}`;
        } else if (data.status === 'timeout') {
          resultEl.innerHTML = `<span class="fail">⏱ ${label} timed out after ${data.elapsed_seconds}s.</span>`;
        } else {
          resultEl.innerHTML = `<span class="fail">✗ ${label} failed (exit ${data.exit_code}) in ${data.elapsed_seconds}s.</span>\n${data.output}`;
        }
        AntigravityTerminal.appendLine(`[Debug] ${label} finished: ${data.status} (exit ${data.exit_code || 0}, ${data.elapsed_seconds}s)`, data.status === 'success' ? 'success' : 'info');
        AntigravityTerminal.appendLine(data.output.split('\n').slice(-8).join('\n'), 'info');
      })
      .catch((err) => {
        resultEl.innerHTML = `<span class="fail">Error: ${err.message}</span>`;
        AntigravityTerminal.appendLine(`[Debug] ${label} error: ${err.message}`, 'info');
      })
      .finally(() => {
        if (button) {
          button.disabled = false;
          button.textContent = 'Run';
        }
      });
  }

  // -------------------------------------------------------------------------
  // Extensions Panel (built-in feature toggles, persisted in localStorage)
  // -------------------------------------------------------------------------
  const EXTENSIONS = [
    { id: 'chat', label: 'Agent Chat Panel', els: ['#agent-chat-panel', '#btn-toggle-chat'] },
    { id: 'terminal', label: 'Terminal', els: ['#terminal-drawer'] },
    { id: 'preview', label: 'Live Preview', els: ['#preview-container'] },
    { id: 'editor', label: 'Monaco Editor', els: ['#monaco-container'] },
    { id: 'settings', label: 'Model Settings', els: ['#act-settings'] },
  ];

  function extStorageKey() {
    return 'antigravity.ext.hidden';
  }

  function getHiddenExts() {
    try {
      return JSON.parse(localStorage.getItem(extStorageKey()) || '[]');
    } catch (err) {
      return [];
    }
  }

  function setHiddenExts(list) {
    localStorage.setItem(extStorageKey(), JSON.stringify(list));
  }

  function applyExtVisibility() {
    const hidden = getHiddenExts();
    EXTENSIONS.forEach((ext) => {
      const isHidden = hidden.includes(ext.id);
      ext.els.forEach((sel) => {
        const el = document.querySelector(sel);
        if (el) el.classList.toggle('hidden', isHidden);
      });
      const checkbox = document.getElementById(`ext-${ext.id}`);
      if (checkbox) checkbox.checked = !isHidden;
    });
  }

  function initExtensions() {
    const list = document.getElementById('ext-list');
    if (!list) return;

    EXTENSIONS.forEach((ext) => {
      const row = document.createElement('div');
      row.className = 'ext-item';
      const label = document.createElement('label');
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.id = `ext-${ext.id}`;
      checkbox.checked = !getHiddenExts().includes(ext.id);
      checkbox.addEventListener('change', () => {
        const hidden = getHiddenExts();
        const idx = hidden.indexOf(ext.id);
        if (checkbox.checked && idx >= 0) hidden.splice(idx, 1);
        if (!checkbox.checked && idx < 0) hidden.push(ext.id);
        setHiddenExts(hidden);
        applyExtVisibility();
      });
      label.appendChild(checkbox);
      label.appendChild(document.createTextNode(ext.label));
      row.appendChild(label);
      list.appendChild(row);
    });

    applyExtVisibility();
  }

  // -------------------------------------------------------------------------
  // Header / Explorer / Preview (existing)
  // -------------------------------------------------------------------------
  function bindHeaderActions() {
    const deployBtn = document.getElementById('btn-deploy-gpu');
    if (deployBtn) {
      deployBtn.addEventListener('click', triggerDeploy);
    }

    const clearTermBtn = document.getElementById('btn-clear-term');
    if (clearTermBtn) {
      clearTermBtn.addEventListener('click', () => {
        AntigravityTerminal.clear();
      });
    }

    const searchBar = document.getElementById('search-bar');
    if (searchBar) {
      searchBar.addEventListener('click', () => {
        AntigravityChat.openPanel();
      });
    }
  }

  function triggerDeploy() {
    AntigravityTerminal.appendLine('[Deploy] Initializing One-Click GPU Deployment to Kaggle / Colab...', 'info');
    fetch('/api/status')
      .then((r) => r.json())
      .then((st) => {
        AntigravityTerminal.appendLine(`[Deploy] Models: ${JSON.stringify(st.models)}`, 'success');
        AntigravityTerminal.appendLine('[Deploy] Kaggle Notebook: notebooks/kaggle_template.ipynb (GPU T4 enabled)', 'success');
        AntigravityTerminal.appendLine('[Deploy] Colab Notebook: notebooks/colab_template.ipynb (GPU T4 enabled)', 'success');
        AntigravityTerminal.appendLine('[Deploy] To deploy directly via CLI: python deploy.py --both --open', 'info');
      });
  }

  function bindExplorerActions() {
    const refreshBtn = document.getElementById('btn-refresh-tree');
    if (refreshBtn) refreshBtn.addEventListener('click', refreshFiles);

    const newFileBtn = document.getElementById('btn-new-file');
    if (newFileBtn) {
      newFileBtn.addEventListener('click', () => {
        const fname = prompt('Enter new file name:');
        if (fname) {
          saveFile(fname, '').then(() => {
            refreshFiles();
            loadFile(fname);
          });
        }
      });
    }

    const newFolderBtn = document.getElementById('btn-new-folder');
    if (newFolderBtn) {
      newFolderBtn.addEventListener('click', () => {
        const folderName = prompt('Enter new folder name:');
        if (folderName) {
          saveFile(`${folderName}/.gitkeep`, '').then(() => {
            refreshFiles();
          });
        }
      });
    }
  }

  function bindLivePreview() {
    const reloadBtn = document.getElementById('btn-reload-preview');
    if (reloadBtn) {
      reloadBtn.addEventListener('click', refreshPreview);
    }
  }

  function refreshFiles() {
    const container = document.getElementById('file-tree-root');
    if (!container) return;

    fetch('/api/files')
      .then((res) => res.json())
      .then((data) => {
        container.innerHTML = '';
        if (data.files && data.files.length > 0) {
          renderTree(data.files, container, 0);
        } else {
          container.innerHTML = '<div class="empty-tree-hint">No files found. Prompt the swarm to generate code!</div>';
        }
      })
      .catch((err) => {
        container.innerHTML = `<div class="empty-tree-hint">Error reading files: ${err.message}</div>`;
      });
  }

  function renderTree(nodes, parentEl, depth) {
    nodes.forEach((node) => {
      const row = document.createElement('div');
      row.className = 'tree-item-row';
      row.style.paddingLeft = `${depth * 12 + 8}px`;

      if (node.isDirectory) {
        row.innerHTML = `
          <i class="codicon codicon-chevron-down" style="font-size:10px;color:#8b949e"></i>
          <i class="codicon codicon-folder" style="color:#dcb67a"></i>
          <span style="overflow:hidden;text-overflow:ellipsis;">${node.name}</span>
        `;
        parentEl.appendChild(row);

        const childContainer = document.createElement('div');
        row.addEventListener('click', () => {
          childContainer.style.display = childContainer.style.display === 'none' ? 'block' : 'none';
        });

        if (node.children && node.children.length > 0) {
          renderTree(node.children, childContainer, depth + 1);
        }
        parentEl.appendChild(childContainer);
      } else {
        row.innerHTML = `
          <i class="codicon codicon-file" style="color:#8b949e;margin-left:14px;"></i>
          <span style="overflow:hidden;text-overflow:ellipsis;">${node.name}</span>
        `;
        row.addEventListener('click', () => {
          loadFile(node.path);
        });
        parentEl.appendChild(row);
      }
    });
  }

  function openContent(filePath, content) {
    activeFilePath = filePath;
    const title = document.getElementById('active-file-title');
    if (title) title.textContent = `Antigravity IDE - ${filePath}`;

    AntigravityEditor.openFile(filePath, content);
    addEditorTab(filePath);
    AntigravityTerminal.appendLine(`[Editor] Opened ${filePath}`, 'info');

    if (filePath.endsWith('.html') || filePath.endsWith('.css') || filePath.endsWith('.js')) {
      refreshPreview();
    }
  }

  function loadFile(filePath) {
    return fetch(`/api/file/${encodeURIComponent(filePath)}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'success') {
          openContent(filePath, data.content);
        } else {
          AntigravityTerminal.appendLine(`[Error] Failed to read ${filePath}: ${data.detail || 'not found'}`, 'info');
        }
      })
      .catch((err) => {
        AntigravityTerminal.appendLine(`[Error] Failed to read ${filePath}: ${err.message}`, 'info');
      });
  }

  function addEditorTab(filePath) {
    const tabsList = document.getElementById('editor-tabs-list');
    if (!tabsList) return;

    const existing = document.getElementById(`tab-${filePath.replace(/[^a-zA-Z0-9]/g, '_')}`);
    document.querySelectorAll('.editor-tab').forEach((t) => t.classList.remove('active'));

    if (existing) {
      existing.classList.add('active');
    } else {
      const tab = document.createElement('div');
      tab.className = 'editor-tab active';
      tab.id = `tab-${filePath.replace(/[^a-zA-Z0-9]/g, '_')}`;
      tab.innerHTML = `
        <i class="codicon codicon-file"></i>
        <span>${filePath.split('/').pop()}</span>
        <span style="font-size:11px;margin-left:6px;cursor:pointer;">✕</span>
      `;
      tab.addEventListener('click', (e) => {
        if (e.target.textContent === '✕') {
          tab.remove();
        } else {
          loadFile(filePath);
        }
      });
      tabsList.appendChild(tab);
    }
  }

  function saveFile(filePath, content) {
    return fetch(`/api/file/${encodeURIComponent(filePath)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: content }),
    })
      .then((res) => res.json())
      .then((data) => {
        AntigravityTerminal.appendLine(`[Saved] ${filePath} saved natively to disk`, 'success');
        refreshPreview();
        return data;
      })
      .catch((err) => {
        AntigravityTerminal.appendLine(`[Save Error] ${err.message}`, 'info');
      });
  }

  function refreshPreview() {
    const frame = document.getElementById('preview-frame');
    if (!frame) return;

    fetch('/api/file/index.html')
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'success' && data.content) {
          let html = data.content;
          // Injected relative styles if style.css exists
          fetch('/api/file/style.css')
            .then((r) => r.json())
            .then((s) => {
              if (s.status === 'success') {
                html = html.replace('</head>', `<style>${s.content}</style></head>`);
              }
              const blob = new Blob([html], { type: 'text/html' });
              frame.src = URL.createObjectURL(blob);
            })
            .catch(() => {
              const blob = new Blob([html], { type: 'text/html' });
              frame.src = URL.createObjectURL(blob);
            });
        }
      })
      .catch(() => {});
  }

  return {
    init,
    refreshFiles,
    loadFile,
    openContent,
    refreshPreview,
  };
})();

document.addEventListener('DOMContentLoaded', () => {
  AntigravityApp.init();
});