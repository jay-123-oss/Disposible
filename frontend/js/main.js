/**
 * Main Application Coordinator for Antigravity IDE
 */

window.AntigravityApp = (function () {
  let activeFilePath = null;
  const openTabs = new Map(); // path -> { name, content }

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

    // 4. Initial Live Preview if index.html exists
    setTimeout(() => {
      refreshPreview();
    }, 1000);
  }

  function bindHeaderActions() {
    const deployBtn = document.getElementById('btn-deploy-gpu');
    if (deployBtn) {
      deployBtn.addEventListener('click', () => {
        AntigravityTerminal.appendLine('[Deploy] Initializing One-Click GPU Deployment to Kaggle / Colab...', 'info');
        fetch('/api/status')
          .then((r) => r.json())
          .then((st) => {
            AntigravityTerminal.appendLine(`[Deploy] Models: ${JSON.stringify(st.models)}`, 'success');
            AntigravityTerminal.appendLine('[Deploy] Kaggle Notebook: notebooks/kaggle_template.ipynb (GPU T4 enabled)', 'success');
            AntigravityTerminal.appendLine('[Deploy] Colab Notebook: notebooks/colab_template.ipynb (GPU T4 enabled)', 'success');
            AntigravityTerminal.appendLine('[Deploy] To deploy directly via CLI: python deploy.py --both --open', 'info');
          });
      });
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

  function loadFile(filePath) {
    activeFilePath = filePath;
    const title = document.getElementById('active-file-title');
    if (title) title.textContent = `Antigravity IDE - ${filePath}`;

    fetch(`/api/file/${encodeURIComponent(filePath)}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'success') {
          AntigravityEditor.openFile(filePath, data.content);
          addEditorTab(filePath);
          AntigravityTerminal.appendLine(`[Editor] Opened ${filePath}`, 'info');

          if (filePath.endsWith('.html') || filePath.endsWith('.css') || filePath.endsWith('.js')) {
            refreshPreview();
          }
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
    refreshPreview,
  };
})();

document.addEventListener('DOMContentLoaded', () => {
  AntigravityApp.init();
});
