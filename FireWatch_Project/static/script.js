/**
 * FireWatch — script.js
 * Dashboard controller: handles API polling, Chart.js graph,
 * Web Audio alert beeps, and all UI state updates.
 */

"use strict";

/* ═══════════════════════════════════════════════════════════════════════
   CONSTANTS & STATE
   ═══════════════════════════════════════════════════════════════════════ */

const API_BASE        = "";          // same origin as Flask
const POLL_INTERVAL   = 1000;        // ms between /api/status calls
const MAX_GRAPH_POINTS = 60;         // seconds of history on graph

let pollTimer         = null;
let alertActive       = false;
let audioCtx          = null;
let beepTimer         = null;
let lastFireState     = false;

/* ═══════════════════════════════════════════════════════════════════════
   CLOCK
   ═══════════════════════════════════════════════════════════════════════ */

function updateClock() {
  const now = new Date();
  document.getElementById("sysClock").textContent =
    now.toTimeString().slice(0, 8);
}
setInterval(updateClock, 1000);
updateClock();

/* ═══════════════════════════════════════════════════════════════════════
   CHART.JS — INTENSITY TIMELINE
   ═══════════════════════════════════════════════════════════════════════ */

const chartCtx = document.getElementById("intensityChart").getContext("2d");

// Gradient fill
function makeGradient(ctx, chartArea) {
  const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
  gradient.addColorStop(0,   "rgba(255,107,0,.55)");
  gradient.addColorStop(.5,  "rgba(255,107,0,.20)");
  gradient.addColorStop(1,   "rgba(255,107,0,.0)");
  return gradient;
}

const chartData = {
  labels:   [],
  datasets: [{
    label:           "Intensity Score",
    data:            [],
    fill:            true,
    backgroundColor: "rgba(255,107,0,.15)",  // replaced after first render
    borderColor:     "#ff6b00",
    borderWidth:     2,
    pointRadius:     2,
    pointHoverRadius: 5,
    pointBackgroundColor: "#ff6b00",
    tension:         0.4,
  }]
};

const intensityChart = new Chart(chartCtx, {
  type: "line",
  data: chartData,
  options: {
    responsive:          true,
    maintainAspectRatio: false,
    animation:           { duration: 300 },
    scales: {
      x: {
        ticks:  { color: "#3d5264", font: { family: "'Share Tech Mono'" }, maxTicksLimit: 8 },
        grid:   { color: "rgba(30,45,61,.6)" },
        border: { color: "rgba(30,45,61,.8)" },
      },
      y: {
        min:    0,
        max:    100,
        ticks:  { color: "#3d5264", font: { family: "'Share Tech Mono'" }, stepSize: 25 },
        grid:   { color: "rgba(30,45,61,.6)" },
        border: { color: "rgba(30,45,61,.8)" },
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "rgba(13,17,23,.92)",
        borderColor:     "rgba(255,107,0,.4)",
        borderWidth:     1,
        titleColor:      "#7a97b0",
        bodyColor:       "#e0eaf5",
        titleFont:       { family: "'Share Tech Mono'" },
        bodyFont:        { family: "'Rajdhani'" },
        callbacks: {
          label: ctx => ` Score: ${ctx.parsed.y}`,
        }
      }
    }
  }
});

// Apply gradient after first draw
intensityChart.options.animation.onComplete = (ctx) => {
  if (!ctx?.chart?.chartArea) return;
  const ds = intensityChart.data.datasets[0];
  ds.backgroundColor = makeGradient(chartCtx, ctx.chart.chartArea);
  intensityChart.update("none");
};

/**
 * Add a data point to the chart and trim to MAX_GRAPH_POINTS.
 */
function pushChartPoint(value) {
  const now    = new Date();
  const label  = now.toTimeString().slice(0, 8);
  chartData.labels.push(label);
  chartData.datasets[0].data.push(value);
  if (chartData.labels.length > MAX_GRAPH_POINTS) {
    chartData.labels.shift();
    chartData.datasets[0].data.shift();
  }
  intensityChart.update();
}

function clearGraph() {
  chartData.labels    = [];
  chartData.datasets[0].data = [];
  intensityChart.update();
  addLog("Graph cleared.", "info");
}

/* ═══════════════════════════════════════════════════════════════════════
   EVENT LOG
   ═══════════════════════════════════════════════════════════════════════ */

function addLog(msg, type = "info") {
  const log  = document.getElementById("eventLog");
  const now  = new Date().toTimeString().slice(0, 8);
  const div  = document.createElement("div");
  div.className   = `log-entry log-${type}`;
  div.innerHTML   = `<span class="log-time">${now}</span>
                     <span class="log-msg">${msg}</span>`;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;

  // Keep log from growing indefinitely
  while (log.children.length > 200) log.removeChild(log.firstChild);
}

function clearLog() {
  document.getElementById("eventLog").innerHTML = "";
  addLog("Log cleared.", "info");
}

/* ═══════════════════════════════════════════════════════════════════════
   WEB AUDIO — ALERT BEEP
   ═══════════════════════════════════════════════════════════════════════ */

function ensureAudioContext() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (audioCtx.state === "suspended") audioCtx.resume();
}

function playBeep(freq = 880, duration = 0.12, volume = 0.35) {
  ensureAudioContext();
  const osc   = audioCtx.createOscillator();
  const gain  = audioCtx.createGain();
  osc.connect(gain);
  gain.connect(audioCtx.destination);
  osc.type      = "square";
  osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
  gain.gain.setValueAtTime(volume, audioCtx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
  osc.start();
  osc.stop(audioCtx.currentTime + duration);
}

function startAlertBeeps() {
  if (beepTimer) return;
  playBeep(1100, .08, .4);
  beepTimer = setInterval(() => {
    playBeep(1100, .08, .4);
    setTimeout(() => playBeep(880, .08, .35), 150);
  }, 800);
}

function stopAlertBeeps() {
  clearInterval(beepTimer);
  beepTimer = null;
}

/* ═══════════════════════════════════════════════════════════════════════
   UI UPDATERS
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Map intensity label → numeric 0-100 for the bar when
 * the server returns only a label (fallback).
 */
const INTENSITY_MAP = { None: 0, Low: 25, Medium: 60, High: 90 };

/**
 * Main UI update — called after every /api/status poll.
 */
function applyStatus(data) {
  const { fire_detected, confidence, intensity, intensity_value, fps, frame_count } = data;

  /* ── FPS & frame counter ──────────────────────────────────────────── */
  document.getElementById("fpsBadge").textContent    = `${fps} FPS`;
  document.getElementById("frameCount").textContent  = frame_count.toLocaleString();

  /* ── Graph ────────────────────────────────────────────────────────── */
  const graphValue = intensity_value ?? INTENSITY_MAP[intensity] ?? 0;
  pushChartPoint(graphValue);

  /* ── Confidence bar ───────────────────────────────────────────────── */
  const confPct = Math.round(confidence * 100);
  document.getElementById("confidenceVal").textContent = `${confPct}%`;
  document.getElementById("confBar").style.width       = `${confPct}%`;

  /* ── Intensity bar & label ────────────────────────────────────────── */
  const intLabel = intensity === "None" ? "—" : intensity.toUpperCase();
  document.getElementById("intensityLevel").textContent = intLabel;
  document.getElementById("intensityBar").style.width   = `${graphValue}%`;

  const intBox = document.getElementById("statIntensity");
  intBox.classList.remove("intensity-low", "intensity-medium", "intensity-high");
  if (intensity !== "None") intBox.classList.add(`intensity-${intensity.toLowerCase()}`);

  // Bar colour
  const barEl    = document.getElementById("intensityBar");
  const barColor = { Low: "#00e676", Medium: "#ffd600", High: "#ff2233" };
  barEl.style.background = barColor[intensity] || "#ff6b00";

  /* ── Fire status ──────────────────────────────────────────────────── */
  const fireStatusEl  = document.getElementById("fireStatus");
  const statFireEl    = document.getElementById("statFire");
  const alertBanner   = document.getElementById("alertBanner");
  const videoCard     = document.getElementById("videoCard");

  if (fire_detected) {
    fireStatusEl.textContent = "FIRE!";
    document.getElementById("statFire").querySelector(".stat-icon").textContent = "🔴";
    statFireEl.classList.add("fire-active");
    alertBanner.classList.add("visible");
    videoCard.classList.add("fire-active");

    if (!alertActive) {
      alertActive = true;
      startAlertBeeps();
      addLog(`🔥 FIRE DETECTED — Intensity: ${intensity}  Confidence: ${confPct}%`, "fire");
    }
  } else {
    fireStatusEl.textContent = "NO FIRE";
    document.getElementById("statFire").querySelector(".stat-icon").textContent = "🟢";
    statFireEl.classList.remove("fire-active");
    alertBanner.classList.remove("visible");
    videoCard.classList.remove("fire-active");

    if (alertActive) {
      alertActive = false;
      stopAlertBeeps();
      addLog("✅ Fire cleared — no fire detected.", "ok");
    }
  }

  lastFireState = fire_detected;
}

/* ═══════════════════════════════════════════════════════════════════════
   API CALLS
   ═══════════════════════════════════════════════════════════════════════ */

async function fetchStatus() {
  try {
    const resp = await fetch(`${API_BASE}/api/status`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    applyStatus(data);
  } catch (err) {
    console.warn("[FireWatch] Status poll failed:", err.message);
  }
}

/**
 * Start detection: call backend, show stream, begin polling.
 */
async function startDetection() {
  // Unlock audio context on user gesture
  ensureAudioContext();

  try {
    const resp = await fetch(`${API_BASE}/api/start`, { method: "POST" });
    const data = await resp.json();
    if (data.status === "started" || data.status === "already_running") {
      showStream();
      enablePolling();
      setButtonState(true);
      addLog("▶ Detection started.", "ok");
    }
  } catch (err) {
    addLog(`⚠ Could not reach backend: ${err.message}`, "warn");
  }
}

/**
 * Stop detection: call backend, hide stream, stop polling.
 */
async function stopDetection() {
  try {
    await fetch(`${API_BASE}/api/stop`, { method: "POST" });
  } catch (_) { /* ignore */ }

  stopPolling();
  hideStream();
  setButtonState(false);
  stopAlertBeeps();
  alertActive = false;

  document.getElementById("alertBanner").classList.remove("visible");
  document.getElementById("videoCard").classList.remove("fire-active");
  document.getElementById("fireStatus").textContent = "NO FIRE";
  document.getElementById("intensityLevel").textContent = "—";
  document.getElementById("confidenceVal").textContent  = "0%";
  document.getElementById("intensityBar").style.width   = "0%";
  document.getElementById("confBar").style.width        = "0%";
  document.getElementById("statFire").classList.remove("fire-active");

  addLog("■ Detection stopped.", "info");
}

/* ═══════════════════════════════════════════════════════════════════════
   STREAM CONTROL
   ═══════════════════════════════════════════════════════════════════════ */

function showStream() {
  const img     = document.getElementById("videoStream");
  const overlay = document.getElementById("videoOverlay");
  const liveBadge = document.getElementById("liveBadge");

  // Append timestamp to bust cache / ensure fresh stream
  img.src         = `${API_BASE}/video_feed?t=${Date.now()}`;
  overlay.classList.add("hidden");
  liveBadge.textContent = "● LIVE";
  liveBadge.classList.add("active");
}

function hideStream() {
  const img     = document.getElementById("videoStream");
  const overlay = document.getElementById("videoOverlay");
  const liveBadge = document.getElementById("liveBadge");

  img.src = "";
  overlay.classList.remove("hidden");
  liveBadge.textContent = "● IDLE";
  liveBadge.classList.remove("active");
}

/* ═══════════════════════════════════════════════════════════════════════
   POLLING
   ═══════════════════════════════════════════════════════════════════════ */

function enablePolling() {
  if (pollTimer) return;
  fetchStatus();                                // immediate first call
  pollTimer = setInterval(fetchStatus, POLL_INTERVAL);
}

function stopPolling() {
  clearInterval(pollTimer);
  pollTimer = null;
}

/* ═══════════════════════════════════════════════════════════════════════
   BUTTON STATE
   ═══════════════════════════════════════════════════════════════════════ */

function setButtonState(running) {
  document.getElementById("btnStart").disabled = running;
  document.getElementById("btnStop").disabled  = !running;
}

/* ═══════════════════════════════════════════════════════════════════════
   INIT
   ═══════════════════════════════════════════════════════════════════════ */

addLog("System initialised. Ready.", "info");
