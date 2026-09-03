/**
 * 6-Agent Swarm Chat & Real-Time Telemetry Module for Antigravity IDE
 */

window.AntigravityChat = (function () {
  let ws = null;
  let isConnected = false;
  let chatPanel = null;
  let chatStream = null;
  let statusDot = null;
  let statusLabel = null;
  let stagedCard = null;
  let stagedContainer = null;
  let stagedCount = null;
  let chatInput = null;
  let lastSessionId = 'default';

  function init() {
    chatPanel = document.getElementById('agent-chat-panel');
    chatStream = document.getElementById('chat-stream');
    statusDot = document.getElementById('status-dot');
    statusLabel = document.getElementById('status-label');
    stagedCard = document.getElementById('staged-changes-card');
    stagedContainer = document.getElementById('staged-files-container');
    stagedCount = document.getElementById('staged-count');
    chatInput = document.getElementById('chat-input');

    // Bind Top-Right Toggle Button
    const toggleBtn = document.getElementById('btn-toggle-chat');
    const closeBtn = document.getElementById('btn-close-chat');
    const newChatBtn = document.getElementById('btn-new-chat');

    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        chatPanel.classList.toggle('open');
        if (chatPanel.classList.contains('open')) {
          chatInput?.focus();
        }
      });
    }

    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        chatPanel.classList.remove('open');
      });
    }

    if (newChatBtn) {
      newChatBtn.addEventListener('click', () => {
        chatStream.innerHTML = '';
        appendMessage('👋 Started a new session. How can the 6-Agent Swarm assist you?', 'agent');
        hideStagedChanges();
        updateStatus('idle', 'Ready. Ask me anything.');
      });
    }

    // Bind Form Submit
    const form = document.getElementById('chat-form');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const prompt = chatInput.value.trim();
        if (!prompt) return;
        submitPrompt(prompt);
      });
    }

    if (chatInput) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          const prompt = chatInput.value.trim();
          if (prompt) submitPrompt(prompt);
        }
      });
    }

    // Bind Accept / Reject Buttons
    const acceptBtn = document.getElementById('btn-accept-changes');
    const rejectBtn = document.getElementById('btn-reject-changes');

    if (acceptBtn) {
      acceptBtn.addEventListener('click', handleAccept);
    }

    if (rejectBtn) {
      rejectBtn.addEventListener('click', handleReject);
    }

    // Connect WebSocket
    connectWebSocket();
  }

  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        isConnected = true;
        AntigravityTerminal.appendLine('[WebSocket connected to Antigravity Swarm on /ws]', 'success');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleIncomingWsMessage(data);
      };

      ws.onclose = () => {
        isConnected = false;
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (err) => {
        console.warn('[Chat WS Error]', err);
      };
    } catch (err) {
      console.warn('[WS init error]', err);
    }
  }

  function handleIncomingWsMessage(data) {
    if (data.type === 'user_message') {
      appendMessage(data.text, 'user');
    } else if (data.type === 'agent_message') {
      appendMessage(data.text, 'agent');
    } else if (data.type === 'status_update') {
      updateStatus(data.lifecycle, data.text);
      AntigravityTerminal.appendLine(`[Swarm] ${data.text}`, 'info');
    } else if (data.type === 'swarm_completed') {
      updateStatus('done', '✅ Task completed! Staged files ready for review.');
      appendMessage(data.text, 'agent');
      if (data.session_id) lastSessionId = data.session_id;
      showStagedChanges(data.deltas || []);

      AntigravityTerminal.appendLine(`[Swarm] Completed generation: ${data.files ? data.files.join(', ') : ''}`, 'success');
      AntigravityTerminal.appendLine(`[Swarm] Quality Score: ${data.quality_score} | Security: ${data.security_status}`, 'success');
    } else if (data.type === 'action_result') {
      appendMessage(data.text, 'agent');
      hideStagedChanges();
      if (data.status === 'accepted') {
        AntigravityApp.refreshFiles();
        // If index.html or main.py generated, open it
        if (data.files && data.files.length > 0) {
          AntigravityApp.loadFile(data.files[0]);
          AntigravityApp.refreshPreview();
        }
      }
    }
  }

  function submitPrompt(prompt) {
    if (!prompt) return;
    chatInput.value = '';

    // Make sure panel is open
    chatPanel.classList.add('open');

    if (isConnected && ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'chat', prompt: prompt }));
    } else {
      // REST fallback
      appendMessage(prompt, 'user');
      updateStatus('thinking', '📝 Analyzing your request...');

      fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt }),
      })
        .then((res) => res.json())
        .then((data) => {
          updateStatus('done', '✅ Task completed!');
          appendMessage(data.message, 'agent');
          showStagedChanges(data.deltas || []);
        })
        .catch((err) => {
          updateStatus('error', '❌ Generation error');
          appendMessage(`Error executing swarm: ${err.message}`, 'agent');
        });
    }
  }

  function handleAccept() {
    if (isConnected && ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'accept' }));
    } else {
      fetch('/api/accept', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: lastSessionId }),
      })
        .then((res) => res.json())
        .then((data) => {
          appendMessage(`✅ ${data.message}`, 'agent');
          hideStagedChanges();
          AntigravityApp.refreshFiles();
          if (data.committed_files && data.committed_files.length > 0) {
            AntigravityApp.loadFile(data.committed_files[0]);
            AntigravityApp.refreshPreview();
          }
        });
    }
  }

  function handleReject() {
    if (isConnected && ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'reject' }));
    } else {
      fetch('/api/reject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: lastSessionId }),
      })
        .then((res) => res.json())
        .then((data) => {
          appendMessage(`❌ ${data.message}`, 'agent');
          hideStagedChanges();
        });
    }
  }

  function showStagedChanges(deltas) {
    if (!stagedCard || !stagedContainer) return;
    stagedContainer.innerHTML = '';

    if (!deltas || deltas.length === 0) {
      hideStagedChanges();
      return;
    }

    if (stagedCount) stagedCount.textContent = `${deltas.length} files`;

    deltas.forEach((d) => {
      const row = document.createElement('div');
      row.className = 'diff-row';
      row.innerHTML = `
        <span>📁 ${d.path}</span>
        <div>
          <span class="diff-tag-add">+${d.linesAdded}</span>
          <span class="diff-tag-del">-${d.linesDeleted}</span>
          <span class="diff-tag-stat">[${d.status}]</span>
        </div>
      `;
      row.addEventListener('click', () => {
        AntigravityApp.loadFile(d.path);
      });
      stagedContainer.appendChild(row);
    });

    stagedCard.classList.remove('hidden');
  }

  function hideStagedChanges() {
    if (stagedCard) stagedCard.classList.add('hidden');
  }

  function updateStatus(lifecycle, text) {
    if (statusDot) {
      statusDot.className = `status-indicator-dot ${lifecycle}`;
    }
    if (statusLabel) {
      statusLabel.textContent = text;
    }
  }

  function appendMessage(text, role) {
    if (!chatStream) return;
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role}`;

    // Simple markdown link & bold format
    let formatted = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code style="background:#161b22;padding:2px 4px;border-radius:3px;">$1</code>')
      .replace(/\n/g, '<br>');

    bubble.innerHTML = formatted;
    chatStream.appendChild(bubble);
    chatStream.scrollTop = chatStream.scrollHeight;
  }

  function openPanel() {
    if (chatPanel) {
      chatPanel.classList.add('open');
      chatInput?.focus();
    }
  }

  return {
    init,
    openPanel,
    submitPrompt,
  };
})();
