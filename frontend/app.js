const API_BASE = '/api';

let currentMonitors = [];

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initModal();
  loadStats();
  loadMonitors();
  loadIncidents();
});

function initTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const target = tab.dataset.tab === 'monitors' ? 'paneMonitors' : 'paneIncidents';
      document.getElementById(target)?.classList.add('active');

      if (tab.dataset.tab === 'incidents') loadIncidents();
    });
  });
}

function initModal() {
  const modal = document.getElementById('monitorModal');
  const openBtn = document.getElementById('openMonitorModal');
  const closeBtn = document.getElementById('closeMonitorBtn');
  const cancelBtn = document.getElementById('cancelMonitorBtn');
  const form = document.getElementById('createMonitorForm');

  openBtn?.addEventListener('click', () => modal.classList.add('active'));
  closeBtn?.addEventListener('click', () => modal.classList.remove('active'));
  cancelBtn?.addEventListener('click', () => modal.classList.remove('active'));

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('monName').value.trim();
    const url = document.getElementById('monUrl').value.trim();
    const expected_status = parseInt(document.getElementById('monExpected').value, 10);

    try {
      const res = await fetch(`${API_BASE}/monitors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, url, expected_status })
      });

      if (!res.ok) throw new Error('Failed to create monitor');
      modal.classList.remove('active');
      form.reset();
      await loadStats();
      await loadMonitors();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  });
}

async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    const data = await res.json();
    document.getElementById('statMonitors').innerText = data.totalMonitors;
    document.getElementById('statAvailability').innerText = `${data.overallAvailability}%`;
    document.getElementById('statLatency').innerText = `${data.averageLatencyMs} ms`;
    document.getElementById('statIncidents').innerText = data.activeIncidents;

    const banner = document.getElementById('systemBanner');
    if (data.activeIncidents > 0) {
      banner.className = 'system-status-banner degraded';
      document.getElementById('systemBannerTitle').innerText = `${data.activeIncidents} Active Service Outage(s)`;
      document.getElementById('systemBannerSub').innerText = 'Synthetic probing detected downtime on one or more monitored endpoints.';
    } else {
      banner.className = 'system-status-banner';
      document.getElementById('systemBannerTitle').innerText = 'All Systems Operational';
      document.getElementById('systemBannerSub').innerText = 'Continuous synthetic health probes across all monitored endpoints.';
    }
  } catch (err) {
    console.warn('Failed to load stats', err);
  }
}

async function loadMonitors() {
  const container = document.getElementById('monitorsList');
  try {
    const res = await fetch(`${API_BASE}/monitors`);
    const list = await res.json();
    currentMonitors = list || [];

    if (currentMonitors.length === 0) {
      // Seed default monitors
      const defaults = [
        { name: "Public Gateway Edge", url: "http://127.0.0.1:8000/api/health", expected_status: 200 },
        { name: "Global CDN Asset Origin", url: "http://127.0.0.1:8000/api/stats", expected_status: 200 }
      ];
      for (const d of defaults) {
        await fetch(`${API_BASE}/monitors`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(d)
        });
      }
      return loadMonitors();
    }

    container.innerHTML = currentMonitors.map(m => {
      // Generate 20 synthetic SLA bars
      const bars = Array.from({ length: 20 }).map((_, i) => {
        const isDown = m.status === 'DOWN' && i === 19;
        return `<div class="sla-bar ${isDown ? 'down' : ''}" title="Day ${i + 1}: ${isDown ? 'Down' : 'Operational'}"></div>`;
      }).join('');

      return `
        <div class="monitor-card">
          <div class="mon-top">
            <div class="mon-info">
              <h3>${escapeHtml(m.name)}</h3>
              <div class="mon-url">${escapeHtml(m.url)}</div>
            </div>
            <div class="mon-actions">
              <span class="badge ${m.status === 'UP' ? 'badge-up' : 'badge-down'}">${m.status}</span>
              <button class="btn btn-secondary btn-sm" onclick="checkMonitor('${m.id}')">⚡ Probe Now</button>
            </div>
          </div>
          <div class="mon-sla-row">
            <div><strong>90-Day SLA:</strong> <span style="color:var(--accent-emerald); font-weight:700;">${m.uptime_pct}%</span></div>
            <div class="sla-bars">${bars}</div>
            <div class="text-mono">Avg: <strong>${m.avg_latency_ms} ms</strong></div>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = `<div style="color: var(--accent-red); padding: 2rem;">Error loading monitors: ${err.message}</div>`;
  }
}

window.checkMonitor = async function(id) {
  try {
    const res = await fetch(`${API_BASE}/monitors/${id}/check`, { method: 'POST' });
    if (!res.ok) throw new Error('Probe failed');
    const data = await res.json();
    alert(`Probe Complete!\nStatus: ${data.status}\nHTTP Code: ${data.probe.status_code}\nLatency: ${data.probe.latency_ms} ms`);
    await loadStats();
    await loadMonitors();
    await loadIncidents();
  } catch (err) {
    alert(`Probe error: ${err.message}`);
  }
};

async function loadIncidents() {
  const tbody = document.getElementById('incidentsTableBody');
  try {
    const res = await fetch(`${API_BASE}/incidents`);
    const list = await res.json();

    if (!list || list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem; color: var(--text-secondary);">No active or historical incidents recorded. Zero downtime.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(inc => `
      <tr>
        <td><span class="badge ${inc.resolved_at ? 'badge-up' : 'badge-down'}">${inc.resolved_at ? 'RESOLVED' : 'ACTIVE OUTAGE'}</span></td>
        <td><strong>${escapeHtml(inc.title)}</strong></td>
        <td>${escapeHtml(inc.cause)}</td>
        <td>${new Date(inc.started_at).toLocaleString()}</td>
        <td>${inc.resolved_at ? new Date(inc.resolved_at).toLocaleString() : 'Investigating...'}</td>
        <td class="text-mono">${inc.duration_seconds ? `${inc.duration_seconds}s` : 'Ongoing'}</td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="color: var(--accent-red);">Failed to load incidents: ${err.message}</td></tr>`;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
