const { contextBridge, ipcRenderer } = require('electron');

/**
 * Antigravity+ Secure Preload IPC Bridge (Section 7 Specification)
 * Strictly exposes native OS file operations, terminal channel, and window controls
 * without browser sandboxing or permission dialogs.
 */
contextBridge.exposeInMainWorld('electron', {
  // Current Working Directory
  getCwd: () => ipcRenderer.invoke('app:getCwd'),

  // Native OS Directory Picker (Zero Browser Permissions)
  openFolder: () => ipcRenderer.invoke('dialog:openFolder'),

  // Recursive Disk Scanner
  readDirRecursive: (folderPath) => ipcRenderer.invoke('fs:readDirRecursive', folderPath),

  // File I/O
  readFile: (filePath) => ipcRenderer.invoke('fs:readFile', filePath),
  writeFile: (filePath, data) => ipcRenderer.invoke('fs:writeFile', filePath, data),
  deleteItem: (itemPath) => ipcRenderer.invoke('fs:deleteItem', itemPath),
  renameItem: (oldPath, newPath) => ipcRenderer.invoke('fs:renameItem', oldPath, newPath),

  // Canonical Multi-Agent Orchestration Channel
  executeAgentPrompt: (prompt) => ipcRenderer.invoke('agent:executePrompt', prompt),

  // Terminal PTY Channel
  sendTerminalInput: (command) => ipcRenderer.send('terminal:input', command),
  onTerminalOutput: (callback) => ipcRenderer.on('terminal:output', (_, data) => callback(data)),

  // Native Window Management
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close'),
});
