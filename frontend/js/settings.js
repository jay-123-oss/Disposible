/**
 * Model Settings Panel — pick the LLM provider, paste your API key, and see
 * live backend status from /api/settings/llm (which mirrors /api/status.llm).
 *
 * Keys are stored in the local .env file by POST /api/settings/llm and are
 * never echoed back — the UI only ever shows the masked suffix.
 */

window.AntigravitySettings = (function () {
  let modal = null;
  let providerSel = null;
  let keyInput = null;
  let keyRow = null;
  let keyEnvTag = null;
  let keySavedHint = null;
  let keyHint = null;
  let clearKeyBtn = null;
  let modelInput = null;
  let modelDefaultTag = null;
  let baseUrlRow = null;
  let baseUrlInput = null;
  let saveMsg = null;
  let modeText = null;
  let detailText = null;
  let statusDot = null;
  let providers = []; // option metadata from the server
  let currentStatus = null; // last llm status payload
  let keyVisible = false;
  let providerInitialized = false; // select is seeded from server status only once

  function $(id) { return document.getElementById(id); }

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function providerMeta(id) {
    return providers.find(function (p) { return p.id === id; }) || null;
  }

  function setStatus(ok, text, detail, provider) {
    statusDot.className = 'status-indicator-dot ' + (ok ? 'ok' : ok === false ? 'error' : 'idle');
    modeText.textContent = text;
    detailText.textContent = detail || '';
    const pill = $('swarm-model-pill');
    if (pill) {
      const label = providerMeta(provider || currentStatus?.provider);
      pill.innerHTML = '<i class="codicon codicon-hubot"></i> ' +
        '6-Agent Swarm · ' + escapeHtml(label ? label.label : (currentStatus?.provider || ''));
    }
  }

  // -------------------------------------------------------------------------
  // Rendering
  // -------------------------------------------------------------------------

  function renderProviderSpecific() {
    const pid = providerSel.value;
    const meta = providerMeta(pid);
    if (!meta) return;

    const needsKey = meta.needs_key && pid !== 'ollama';
    keyRow.classList.toggle('hidden', !needsKey);
    baseUrlRow.classList.toggle('hidden', !meta.needs_base_url);
    baseUrlInput.placeholder = 'https://api.example.com/v1';
    // Prefill the base URL only when the active backend already IS this
    // openai-compatible endpoint; otherwise start blank.
    baseUrlInput.value = (currentStatus && currentStatus.provider === 'openai-compatible' && pid === 'openai-compatible' && currentStatus.base_url)
      ? currentStatus.base_url
      : '';
    $('set-baseurl-hint').textContent = meta.needs_base_url
      ? 'Required for custom / self-hosted OpenAI-compatible endpoints.'
      : '';

    // Key env var + placeholder + saved indicator
    keyEnvTag.textContent = meta.key_env ? meta.key_env + ':' : '';
    const keyConfigured = currentStatus && currentStatus.key_configured && currentStatus.provider === pid;
    keySavedHint.textContent = keyConfigured && currentStatus.key_masked
      ? 'saved: ' + currentStatus.key_masked
      : '';
    clearKeyBtn.classList.toggle('hidden', !keyConfigured);
    keyHint.textContent = pid === 'openai-compatible'
      ? 'May be empty for local endpoints (LM Studio / vLLM).'
      : (meta.needs_key ? 'Stored in your local .env — never sent to anyone but the provider.' : '');
    if (!needsKey) {
      keyInput.value = ''; // providers without a key must never submit a stale key
      keySavedHint.textContent = '';
    } else if (!keyConfigured) {
      keyInput.value = '';
    }

    // Model placeholder + hint. The input itself always starts blank — leaving
    // it empty means "use the provider default" (or the LLM_MODEL override if
    // one is already configured).
    modelInput.placeholder = meta.default_model
      ? 'Default: ' + meta.default_model
      : 'Required for this provider (no default)';
    modelDefaultTag.textContent = meta.default_model ? 'default: ' + meta.default_model : 'no provider default';

    // Status line, prefilled from the last /api/settings/llm fetch
    if (currentStatus) {
      if (currentStatus.mode === 'cloud-api-key') {
        setStatus(true, 'Active: ' + (meta && meta.id === currentStatus.provider ? meta.label : currentStatus.provider) + ' (API key)', keyConfigured ? 'Key ' + currentStatus.key_masked + ' — agents use hosted models.' : 'Key configured — agents use hosted models.', pid);
      } else if (currentStatus.mode === 'local-ollama') {
        setStatus(true, 'Local Ollama runtime (no key needed)', 'Model: ' + (currentStatus.model || 'qwen2.5-coder:3b') + ' at ' + (currentStatus.base_url || 'http://localhost:11434'), pid);
      } else {
        setStatus(false, 'Provider selected but no API key', 'Set ' + (meta ? meta.key_env : '') + ' below and Save.', pid);
      }
    }
  }

  function renderProviders() {
    providerSel.innerHTML = '';
    providers.forEach(function (p) {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.label;
      providerSel.appendChild(opt);
    });
    // Seed the select from the live backend on first load only — never clobber
    // the user's in-progress choice when they switch providers.
    if (!providerInitialized && currentStatus && currentStatus.provider) {
      providerSel.value = currentStatus.provider;
      providerInitialized = true;
    }
  }

  function refresh() {
    saveMsg.textContent = '';
    saveMsg.className = 'settings-save-msg';
    setStatus(true, 'Checking backend…', '', providerSel.value);
    fetch('/api/settings/llm')
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (data) {
        providers = data.providers || [];
        currentStatus = data.llm || {};
        renderProviders();
        renderProviderSpecific();
      })
      .catch(function (err) {
        setStatus(false, 'Cannot reach settings API', String(err && err.message || err));
      });
  }

  // -------------------------------------------------------------------------
  // Actions
  // -------------------------------------------------------------------------

  function showMessage(text, isError) {
    saveMsg.textContent = text;
    saveMsg.className = 'settings-save-msg ' + (isError ? 'error' : 'ok');
  }

  function onSave(ev) {
    ev.preventDefault();
    const pid = providerSel.value;
    const payload = {
      provider: pid,
      model: modelInput.value.trim(),
    };
    if (pid === 'openai-compatible') {
      payload.base_url = baseUrlInput.value.trim();
    }
    // Only send the key when the user actually typed something new.
    if (keyInput.value.trim()) {
      payload.api_key = keyInput.value.trim();
    }

    showMessage('Saving…');
    fetch('/api/settings/llm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
      .then(function (res) {
        if (!res.ok) {
          const detail = res.data && res.data.detail;
          showMessage('Save failed: ' + (detail || 'unknown error'), true);
          return;
        }
        currentStatus = res.data.llm || currentStatus;
        keyInput.value = '';
        showMessage('✓ ' + (res.data.message || 'Saved.'));
        renderProviderSpecific();
      })
      .catch(function (err) { showMessage('Save failed: ' + String(err && err.message || err), true); });
  }

  function onClearKey() {
    const pid = providerSel.value;
    showMessage('Removing saved key…');
    fetch('/api/settings/llm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider: pid, clear_key: true }),
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
      .then(function (res) {
        if (!res.ok) { showMessage('Failed to remove key', true); return; }
        currentStatus = res.data.llm || currentStatus;
        showMessage('Key removed.');
        renderProviderSpecific();
      })
      .catch(function (err) { showMessage('Failed to remove key: ' + String(err && err.message || err), true); });
  }

  function toggleKeyVisibility() {
    keyVisible = !keyVisible;
    keyInput.type = keyVisible ? 'text' : 'password';
    const icon = keyInput.parentElement.querySelector('.codicon');
    icon.className = 'codicon ' + (keyVisible ? 'codicon-eye-closed' : 'codicon-eye');
  }

  function open() {
    modal.classList.remove('hidden');
    refresh();
  }

  function close() {
    modal.classList.add('hidden');
  }

  function init() {
    modal = $('settings-modal');
    providerSel = $('set-provider');
    keyInput = $('set-api-key');
    keyRow = $('set-key-row');
    keyEnvTag = $('set-key-env');
    keySavedHint = $('set-key-saved');
    keyHint = $('set-key-hint');
    clearKeyBtn = $('btn-clear-key');
    modelInput = $('set-model');
    modelDefaultTag = $('set-model-default');
    baseUrlRow = $('set-baseurl-row');
    baseUrlInput = $('set-base-url');
    saveMsg = $('settings-save-msg');
    modeText = $('settings-mode-text');
    detailText = $('settings-detail-text');
    statusDot = $('settings-status-dot');

    if (!modal) return;

    // Openers: activity-bar gear + a gear in the chat status area is not needed —
    // the activity bar entry is the single entry point.
    const gear = $('act-settings');
    if (gear) gear.addEventListener('click', open);

    $('btn-close-settings').addEventListener('click', close);
    modal.addEventListener('click', function (e) { if (e.target === modal) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !modal.classList.contains('hidden')) close(); });

    providerSel.addEventListener('change', function () {
      modelInput.value = '';
      saveMsg.textContent = '';
      saveMsg.className = 'settings-save-msg';
      // Re-render the fields for the newly selected provider using the data we
      // already have; the status area still reflects the ACTIVE backend until
      // the user hits Save (no extra round-trip, no select clobbering).
      renderProviderSpecific();
    });
    keyInput.addEventListener('input', function () { saveMsg.textContent = ''; });
    modelInput.addEventListener('input', function () { saveMsg.textContent = ''; });
    $('btn-toggle-key').addEventListener('click', toggleKeyVisibility);
    $('btn-clear-key').addEventListener('click', onClearKey);
    $('llm-settings-form').addEventListener('submit', onSave);
  }

  return { init: init, open: open, close: close };
})();

document.addEventListener('DOMContentLoaded', () => {
  window.AntigravitySettings.init();
});
