// Phone app logic: read GPS, pack the 16-byte frame (phone/frame.js), send it to the gateway.

const FIELDS = ["injury", "mobility", "people", "hazard", "needs"];
const DEMO_LOCATION = { lat: 30.4165, lon: 77.968 };   // fallback if GPS is unavailable
let codebook = null;

const $ = (id) => document.getElementById(id);

// Each phone needs a stable device id (0-1023) and a message counter (0-255).
function stored(key, makeDefault) {
  try {
    let v = localStorage.getItem(key);
    if (v === null) { v = String(makeDefault()); localStorage.setItem(key, v); }
    return Number(v);
  } catch { return makeDefault(); }
}
const deviceId = stored("dm-device", () => Math.floor(Math.random() * 1024));
function nextSeq() {
  const seq = (stored("dm-seq", () => 0) + 1) % 256;
  try { localStorage.setItem("dm-seq", String(seq)); } catch {}
  return seq;
}

function fillSelect(id, labels) {
  const sel = $(id);
  labels.forEach((label, code) => sel.add(new Option(label, code)));
}

function currentChoice() {
  const msg = {};
  for (const f of FIELDS) msg[f] = Number($(f).value);
  return msg;
}

function updatePreview() {
  const { injury, mobility } = currentChoice();
  const { priority } = triage(injury, mobility, codebook.injury_priority);
  const label = codebook.priority[priority];
  $("preview").innerHTML = `This report will be sent as <span class="tag ${label}">${label}</span>`;
}

function getLocation() {
  $("lat").value = DEMO_LOCATION.lat;
  $("lon").value = DEMO_LOCATION.lon;
  if (!navigator.geolocation) {
    $("gps").textContent = "GPS not available - using demo location (editable).";
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      $("lat").value = pos.coords.latitude.toFixed(6);
      $("lon").value = pos.coords.longitude.toFixed(6);
      $("gps").textContent = `GPS fix, accurate to about ${Math.round(pos.coords.accuracy)} m.`;
    },
    (err) => { $("gps").textContent = `GPS failed (${err.message}) - using demo location (editable).`; },
    { enableHighAccuracy: true, timeout: 15000 },
  );
}

async function send() {
  const msg = currentChoice();
  const { priority, confidence } = triage(msg.injury, msg.mobility, codebook.injury_priority);
  const now = new Date();
  Object.assign(msg, {
    device: deviceId,
    seq: nextSeq(),
    hops: 0,
    priority,
    confidence,
    time: now.getUTCHours() * 60 + now.getUTCMinutes(),
    lat: Number($("lat").value),
    lon: Number($("lon").value),
  });

  let frame;
  try {
    frame = encodeFrame(msg);
  } catch (e) {
    $("result").innerHTML = `<span class="err">Could not build frame: ${e.message}</span>`;
    return;
  }
  const hex = Array.from(frame, (b) => b.toString(16).padStart(2, "0")).join(" ");

  $("send").disabled = true;
  try {
    const res = await fetch("/frame", {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: frame,
    });
    const body = await res.json();
    const status = res.ok
      ? `<span class="ok">Delivered${body.duplicate ? " (duplicate ignored)" : ""}.</span>`
      : `<span class="err">Rejected: ${body.detail}</span>`;
    $("result").innerHTML = `${status}<br>${frame.length} bytes sent (device ${deviceId}, seq ${msg.seq}):<br><span class="hex">${hex}</span>`;
  } catch (e) {
    $("result").innerHTML = `<span class="err">Gateway unreachable - is the phone on the laptop's hotspot?</span>`;
  } finally {
    $("send").disabled = false;
  }
}

async function init() {
  try {
    codebook = await (await fetch("/codebook")).json();
  } catch {
    $("preview").textContent = "Cannot reach the gateway.";
    return;
  }
  for (const f of FIELDS) fillSelect(f, codebook[f]);
  FIELDS.forEach((f) => $(f).addEventListener("change", updatePreview));
  $("send").addEventListener("click", send);
  $("send").disabled = false;
  updatePreview();
  getLocation();
}

init();
