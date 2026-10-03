// IoT Dashboard: polls the REST API every few seconds and redraws the page.
const REFRESH_MS = 3000;
let selectedDevice = null;
let charts = {};

// ---------- helpers ----------
function fmt(v, d = 1) {
  return v === null || v === undefined ? "--" : Number(v).toFixed(d);
}

// Escape text before putting it in HTML (prevents XSS from device data).
function esc(s) {
  return String(s).replace(/[&<>"']/g, c => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

// The server stores UTC times without a "Z", so add it before parsing.
function toDate(iso) {
  return iso ? new Date(iso.endsWith("Z") ? iso : iso + "Z") : null;
}

function timeAgo(iso) {
  const d = toDate(iso);
  if (!d) return "never";
  const s = Math.max(0, Math.round((Date.now() - d.getTime()) / 1000));
  if (s < 60) return s + "s ago";
  if (s < 3600) return Math.floor(s / 60) + "m ago";
  if (s < 86400) return Math.floor(s / 3600) + "h ago";
  return Math.floor(s / 86400) + "d ago";
}

async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(url + " returned " + r.status);
  return r.json();
}

// ---------- login (needed for Acknowledge / Resolve) ----------
async function ensureToken() {
  let token = sessionStorage.getItem("token");
  if (token) return token;
  const username = prompt("Username (admin):");
  if (!username) return null;
  const password = prompt("Password:");
  if (!password) return null;
  const r = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!r.ok) { alert("Login failed"); return null; }
  token = (await r.json()).access_token;
  sessionStorage.setItem("token", token);
  return token;
}

async function alertAction(id, action) {
  const token = await ensureToken();
  if (!token) return;
  const r = await fetch(`/alerts/${id}/${action}`, {
    method: "PUT",
    headers: { Authorization: "Bearer " + token },
  });
  if (r.status === 401) {
    sessionStorage.removeItem("token");
    alert("Session expired. Click the button again to log in.");
    return;
  }
  refresh();
}

// ---------- charts ----------
function makeChart(canvasId, label, color) {
  return new Chart(document.getElementById(canvasId), {
    type: "line",
    data: { labels: [], datasets: [{ label, data: [], borderColor: color, tension: 0.3, pointRadius: 2 }] },
    options: { animation: false, plugins: { legend: { display: false } } },
  });
}

function initCharts() {
  charts.temperature = makeChart("chart-temp", "Temperature", "#dc2626");
  charts.humidity = makeChart("chart-hum", "Humidity", "#2563eb");
  charts.voltage = makeChart("chart-volt", "Voltage", "#16a34a");
  charts.current = makeChart("chart-curr", "Current", "#f59e0b");
}

async function updateCharts() {
  if (!selectedDevice) return;
  document.getElementById("chart-title").textContent = "(" + selectedDevice + ", last 30 readings)";
  const readings = await getJSON(`/devices/${selectedDevice}/readings?limit=30`);
  readings.reverse(); // API returns newest first, charts need oldest first
  const labels = readings.map(r => toDate(r.timestamp).toLocaleTimeString());
  for (const key of Object.keys(charts)) {
    charts[key].data.labels = labels;
    charts[key].data.datasets[0].data = readings.map(r => r[key]);
    charts[key].update();
  }
}

// ---------- rendering ----------
function deviceStatus(device, activeAlerts) {
  if (device.status === "OFFLINE") return "OFFLINE";
  const mine = activeAlerts.filter(a => a.device_id === device.device_id);
  if (mine.some(a => a.severity === "CRITICAL")) return "CRITICAL";
  if (mine.length > 0) return "WARNING";
  return "ONLINE";
}

function renderCards(devices, latest, active) {
  const online = devices.filter(d => d.status === "ONLINE");
  const critical = active.filter(a => a.severity === "CRITICAL").length;
  const onlineReadings = devices
    .map((d, i) => (d.status === "ONLINE" ? latest[i] : null))
    .filter(r => r);
  const avg = key => {
    const vals = onlineReadings.map(r => r[key]).filter(v => v !== null && v !== undefined);
    return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
  };

  document.getElementById("c-total").textContent = devices.length;
  document.getElementById("c-online").textContent = online.length;
  document.getElementById("c-offline").textContent = devices.length - online.length;
  document.getElementById("c-alerts").textContent = active.length;
  document.getElementById("c-critical").textContent = critical;
  document.getElementById("c-temp").textContent = fmt(avg("temperature"));
  document.getElementById("c-hum").textContent = fmt(avg("humidity"));

  const badge = document.getElementById("health-badge");
  if (critical > 0) { badge.className = "badge badge-crit"; badge.textContent = "System: CRITICAL"; }
  else if (active.length > 0) { badge.className = "badge badge-warn"; badge.textContent = "System: WARNING"; }
  else { badge.className = "badge badge-ok"; badge.textContent = "System: HEALTHY"; }
}

function renderDevices(devices, latest, active) {
  const body = document.getElementById("device-body");
  if (devices.length === 0) {
    body.innerHTML = '<tr><td colspan="8">No devices yet</td></tr>';
    return;
  }
  body.innerHTML = devices.map((d, i) => {
    const r = latest[i] || {};
    const st = deviceStatus(d, active);
    const sel = d.device_id === selectedDevice ? "selected" : "";
    return `<tr class="${sel}" data-id="${esc(d.device_id)}">
      <td>${esc(d.device_id)}</td>
      <td><span class="status status-${st}">${st}</span></td>
      <td>${fmt(r.temperature)}</td><td>${fmt(r.humidity)}</td>
      <td>${fmt(r.voltage)}</td><td>${fmt(r.current)}</td>
      <td>${r.battery === undefined || r.battery === null ? "--" : r.battery + "%"}</td>
      <td>${timeAgo(d.last_seen)}</td>
    </tr>`;
  }).join("");
}

function renderAlerts(active) {
  const body = document.getElementById("alert-body");
  if (active.length === 0) {
    body.innerHTML = '<tr><td colspan="9">No active alerts \u2705</td></tr>';
    return;
  }
  body.innerHTML = active.map(a => {
    const action = a.status === "OPEN"
      ? `<button class="btn" data-id="${a.id}" data-action="acknowledge">Acknowledge</button>`
      : `<button class="btn" data-id="${a.id}" data-action="resolve">Resolve</button>`;
    return `<tr>
      <td>${a.id}</td><td>${esc(a.device_id)}</td><td>${esc(a.alert_type)}</td>
      <td class="sev-${esc(a.severity)}">${esc(a.severity)}</td>
      <td>${fmt(a.actual_value)}</td><td>${fmt(a.threshold_value)}</td>
      <td>${esc(a.status)}</td><td>${timeAgo(a.created_at)}</td><td>${action}</td>
    </tr>`;
  }).join("");
}

// ---------- main loop ----------
async function refresh() {
  try {
    const devices = await getJSON("/devices");
    const allAlerts = await getJSON("/alerts?limit=500");
    const active = allAlerts.filter(a => a.status !== "RESOLVED");
    const latest = await Promise.all(
      devices.map(d => getJSON(`/devices/${d.device_id}/readings?limit=1`).then(r => r[0] || null))
    );

    if (!selectedDevice && devices.length > 0) {
      const firstOnline = devices.find(d => d.status === "ONLINE");
      selectedDevice = (firstOnline || devices[0]).device_id;
    }

    renderCards(devices, latest, active);
    renderDevices(devices, latest, active);
    renderAlerts(active);
    await updateCharts();
    document.getElementById("last-update").textContent =
      "Updated " + new Date().toLocaleTimeString();
  } catch (err) {
    console.error(err);
    document.getElementById("last-update").textContent = "API unreachable";
  }
}

// ---------- events ----------
document.getElementById("device-body").addEventListener("click", e => {
  const row = e.target.closest("tr[data-id]");
  if (!row) return;
  selectedDevice = row.dataset.id;
  refresh();
});

document.getElementById("alert-body").addEventListener("click", e => {
  const btn = e.target.closest("button[data-action]");
  if (!btn) return;
  alertAction(btn.dataset.id, btn.dataset.action);
});

initCharts();
refresh();
setInterval(refresh, REFRESH_MS);