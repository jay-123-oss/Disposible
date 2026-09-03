const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let mainWindow = null;
let activeShell = null;

// The desktop renderer's Accept flow expects staged files as a content map
// { relativePath: content } (same shape CanonicalOrchestrator.execute_prompt returns).
// Newer servers return that map in /api/chat; legacy ones only return file names,
// so hydrate each staged file from the staged-file endpoint (best effort).
async function hydrateStagedFiles(baseUrl, sessionId, files) {
  if (!files) return {};
  // Already a map (or empty object) -> nothing to do.
  if (!Array.isArray(files)) return files;

  const hydrated = {};
  await Promise.all(files.map(async (name) => {
    const params = new URLSearchParams({ session_id: sessionId || 'default', path: name });
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 1500);
    try {
      const resp = await fetch(`${baseUrl}/api/staged-file?${params.toString()}`, { signal: controller.signal });
      if (resp.ok) {
        const data = await resp.json();
        if (data.status === 'success' && typeof data.content === 'string') {
          hydrated[name] = data.content;
        }
      }
    } catch (_) {
      // Best effort: leave the file out of the map if it cannot be fetched.
    } finally {
      clearTimeout(timeout);
    }
  }));
  return hydrated;
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 850,
    minWidth: 960,
    minHeight: 640,
    frame: false, // Borderless custom window frame
    backgroundColor: '#1e1e1e',
    title: 'Antigravity IDE',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  mainWindow.on('closed', () => {
    mainWindow = null;
    if (activeShell) {
      try {
        activeShell.kill();
      } catch (_) {}
      activeShell = null;
    }
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// ============================================================================
// IPC Handlers: Native Window Controls
// ============================================================================
ipcMain.on('window:minimize', () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.on('window:maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.on('window:close', () => {
  if (mainWindow) mainWindow.close();
});

// ============================================================================
// IPC Handlers: Native File System & Directory Dialog (Section 7)
// ============================================================================

ipcMain.handle('app:getCwd', () => {
  return process.cwd().replace(/\\/g, '/');
});

ipcMain.handle('dialog:openFolder', async () => {
  if (!mainWindow) return null;
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'Select Project Folder - Antigravity IDE',
    properties: ['openDirectory'],
  });

  if (result.canceled || !result.filePaths.length) {
    return null;
  }

  return result.filePaths[0];
});

async function scanDirectory(dirPath, maxDepth = 4, currentDepth = 0) {
  try {
    const entries = await fs.promises.readdir(dirPath, { withFileTypes: true });
    const items = [];

    const sortedEntries = entries.sort((a, b) => {
      if (a.isDirectory() === b.isDirectory()) {
        return a.name.localeCompare(b.name);
      }
      return a.isDirectory() ? -1 : 1;
    });

    for (const entry of sortedEntries) {
      if (entry.name === '.git' || (entry.name === 'node_modules' && currentDepth > 0)) continue;

      const fullPath = path.join(dirPath, entry.name).replace(/\\/g, '/');
      const isDir = entry.isDirectory();

      const item = {
        name: entry.name,
        path: fullPath,
        isDirectory: isDir,
        children: isDir ? [] : null,
      };

      if (isDir && currentDepth < maxDepth) {
        item.children = await scanDirectory(fullPath, maxDepth, currentDepth + 1);
      }

      items.push(item);
    }

    return items;
  } catch (err) {
    console.error('Error reading directory:', dirPath, err);
    return [];
  }
}

ipcMain.handle('fs:readDirRecursive', async (event, folderPath) => {
  if (!folderPath) return [];
  return await scanDirectory(folderPath);
});

ipcMain.handle('fs:readFile', async (event, filePath) => {
  try {
    const content = await fs.promises.readFile(filePath, 'utf-8');
    return { success: true, content };
  } catch (err) {
    return { success: false, error: err.message };
  }
});

ipcMain.handle('fs:writeFile', async (event, filePath, data, executionAuth = {}) => {
  try {
    const baseName = path.basename(filePath).toLowerCase();
    // IPC Security Gate: Strictly forbid unauthorized sample.txt creation
    if (baseName === 'sample.txt' && !executionAuth.allowSample) {
      console.warn('[IPC Security Gate] Blocked unauthorized attempt to write sample.txt');
      return { success: false, error: 'IPC Gate: Unauthorized attempt to create sample.txt blocked by safety policy.' };
    }

    // Path traversal check: verify target path is inside workspace
    const resolvedPath = path.resolve(filePath);
    const cwd = process.cwd();
    if (!resolvedPath.toLowerCase().startsWith(cwd.toLowerCase())) {
      console.warn('[IPC Security Gate] Blocked out-of-workspace write attempt:', resolvedPath);
      return { success: false, error: 'IPC Gate: Out-of-workspace file writes are blocked by security policy.' };
    }

    await fs.promises.mkdir(path.dirname(filePath), { recursive: true });
    await fs.promises.writeFile(filePath, data, 'utf-8');
    return { success: true };
  } catch (err) {
    return { success: false, error: err.message };
  }
});

ipcMain.handle('fs:deleteItem', async (event, itemPath) => {
  try {
    await fs.promises.rm(itemPath, { recursive: true, force: true });
    return { success: true };
  } catch (err) {
    return { success: false, error: err.message };
  }
});

ipcMain.handle('fs:renameItem', async (event, oldPath, newPath) => {
  try {
    await fs.promises.rename(oldPath, newPath);
    return { success: true };
  } catch (err) {
    return { success: false, error: err.message };
  }
});

// ============================================================================
// ============================================================================
// IPC Handlers: Terminal Channel (Section 7)
// ============================================================================
ipcMain.on('terminal:input', (event, command) => {
  if (!mainWindow) return;

  const cmdStr = (command || '').trim();
  if (!cmdStr) return;

  mainWindow.webContents.send('terminal:output', `\r\n$ ${cmdStr}\r\n`);

  try {
    const isWin = process.platform === 'win32';
    const shell = isWin ? 'powershell.exe' : '/bin/bash';
    const args = isWin ? ['-NoLogo', '-Command', cmdStr] : ['-c', cmdStr];

    const child = spawn(shell, args, {
      cwd: process.cwd(),
      env: process.env,
      shell: false,
    });

    child.stdout.on('data', (data) => {
      if (mainWindow) {
        mainWindow.webContents.send('terminal:output', data.toString());
      }
    });

    child.stderr.on('data', (data) => {
      if (mainWindow) {
        mainWindow.webContents.send('terminal:output', data.toString());
      }
    });

    child.on('close', (code) => {
      if (mainWindow) {
        mainWindow.webContents.send('terminal:output', `[Process exited with code ${code}]\r\n`);
      }
    });

    child.on('error', (err) => {
      if (mainWindow) {
        mainWindow.webContents.send('terminal:output', `Error: ${err.message}\r\n`);
      }
    });
  } catch (err) {
    mainWindow.webContents.send('terminal:output', `Execution error: ${err.message}\r\n`);
  }
});

// ============================================================================
// IPC Handlers: Canonical Orchestrator Agent Channel
// ============================================================================
ipcMain.handle('agent:executePrompt', async (event, promptText) => {
  const prompt = (promptText || '').trim();
  if (!prompt) return { status: 'error', error: 'Empty prompt' };

  // 1. Try local server first if FastAPI server is active
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 1500);
    const resp = await fetch('http://127.0.0.1:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: prompt, session_id: 'desktop_ui' }),
      signal: controller.signal,
    });
    clearTimeout(timeout);
    if (resp.ok) {
      const result = await resp.json();
      // Normalize to the canonical execute_prompt shape so the renderer can stage
      // and accept files. If the server only returned file names (legacy contract),
      // fetch each staged file's content before handing the result to the renderer.
      const sessionId = result.session_id || 'desktop_ui';
      const serverBaseUrl = 'http://127.0.0.1:8000';
      // Always hand the renderer a content map ({ path: content }) — never a bare
      // name array, which would make the Accept flow write bogus files.
      result.files = await hydrateStagedFiles(serverBaseUrl, sessionId, result.files);
      if (Object.keys(result.files).length > 0) {
        result.files_count = Object.keys(result.files).length;
        result.deltas = result.deltas || Object.keys(result.files).map((name) => ({
          path: name,
          status: 'CREATED',
          linesAdded: (result.files[name] || '').split('\n').length,
          linesDeleted: 0,
        }));
      }
      return result;
    }
  } catch (_) {}

  // 2. Direct Python Canonical Orchestrator Execution Bridge
  return new Promise((resolve) => {
    const pythonBin = process.platform === 'win32' ? 'python' : 'python3';
    const pyScript = `
import sys, json, asyncio
from core.canonical_orchestrator import CanonicalOrchestrator

async def main():
    orch = CanonicalOrchestrator()
    res = await orch.execute_prompt(sys.argv[1])
    print("__JSON_START__" + json.dumps(res) + "__JSON_END__")

asyncio.run(main())
`;
    const proc = spawn(pythonBin, ['-c', pyScript, prompt], {
      cwd: process.cwd(),
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stderr += d.toString(); });

    proc.on('close', (code) => {
      const match = stdout.match(/__JSON_START__([\s\S]*?)__JSON_END__/);
      if (match) {
        try {
          return resolve(JSON.parse(match[1]));
        } catch (e) {
          return resolve({ status: 'error', error: e.message, raw: stdout });
        }
      }
      resolve({
        status: 'error',
        error: stderr || stdout || 'Execution failed',
        code,
      });
    });
  });
});
