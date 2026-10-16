"use strict";

const $ = (id) => document.getElementById(id);
const defaultPoints = [[0, 0, 10], [30, 0, 10], [30, 25, 20], [0, 25, 10]];
let currentRun = null;
let animation = null;
let project = null;
let busy = false;
const svgNS = "http://www.w3.org/2000/svg";

function svgElement(tag, attrs, text) {
  const element = document.createElementNS(svgNS, tag);
  Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value));
  if (text !== undefined) element.textContent = text;
  return element;
}

function readPoints() {
  return [...$("waypoints").children].map((row) => {
    const values = [...row.querySelectorAll("input")].map((input) => Number(input.value));
    return { x_m: values[0], y_m: values[1], z_m: values[2] };
  });
}

function stopPlayback() {
  if (animation !== null) cancelAnimationFrame(animation);
  animation = null;
  $("play").textContent = "▶";
  $("play").setAttribute("aria-label", "Play preview");
}

function drawRoute(points) {
  const group = $("route-elements");
  group.replaceChildren();
  if (points.length < 2 || !points.every((p) => Object.values(p).every(Number.isFinite))) return;
  const xs = points.map((p) => p.x_m), ys = points.map((p) => p.y_m);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  // Equal scale on both axes preserves the route's shape.
  const scale = Math.min(620 / Math.max(maxX - minX, 10), 240 / Math.max(maxY - minY, 10));
  const centerX = (minX + maxX) / 2, centerY = (minY + maxY) / 2;
  project = (p) => [380 + (p.x_m - centerX) * scale, 175 - (p.y_m - centerY) * scale];
  group.append(svgElement("polyline", { points: points.map((p) => project(p).join(",")).join(" "), class: "route-line" }));
  points.forEach((p, index) => {
    const [x, y] = project(p);
    group.append(svgElement("circle", { cx: x, cy: y, r: 5, class: "waypoint-circle" }));
    group.append(svgElement("text", { x: x + 12, y: y - 12, class: "waypoint-label" }, String(index + 1).padStart(2, "0")));
  });
  group.append(svgElement("text", { x: 22, y: 333, class: "axis-label" }, `X ${minX}…${maxX} m · Y ${minY}…${maxY} m`));
  group.append(svgElement("circle", { id: "position-marker", cx: project(points[0])[0], cy: project(points[0])[1], r: 8, class: "position-marker", visibility: currentRun ? "visible" : "hidden" }));
}

function markEdited() {
  if (busy) return;
  stopPlayback();
  currentRun = null;
  $("preview-state").textContent = "NOT RUN";
  $("preview-state").classList.remove("complete");
  $("map-label").textContent = "Planned route";
  $("distance").textContent = "—";
  $("duration").textContent = "—";
  $("point-count").textContent = readPoints().length;
  $("run-label").textContent = "Configuration changed · generate a new preview";
  $("download").disabled = $("play").disabled = $("timeline").disabled = true;
  $("timeline").value = 0;
  $("time-label").textContent = "0.0 s";
  $("altitude-label").textContent = "Z — m";
  $("form-error").hidden = true;
  drawRoute(readPoints());
}

function renderWaypoints(points) {
  $("waypoints").replaceChildren();
  points.forEach((point, index) => {
    const values = Array.isArray(point) ? point : [point.x_m, point.y_m, point.z_m];
    const row = document.createElement("div");
    row.className = "waypoint-row";
    const number = document.createElement("span");
    number.className = "point-number";
    number.textContent = String(index + 1).padStart(2, "0");
    row.append(number);
    values.forEach((value, axis) => {
      const input = document.createElement("input");
      input.type = "number";
      input.step = "any";
      input.required = true;
      input.min = axis === 2 ? "0" : "-500";
      input.max = axis === 2 ? "120" : "500";
      input.value = value;
      input.setAttribute("aria-label", `Waypoint ${index + 1} ${["X", "Y", "altitude"][axis]} in meters`);
      row.append(input);
    });
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "remove";
    remove.textContent = "×";
    remove.setAttribute("aria-label", `Remove waypoint ${index + 1}`);
    remove.disabled = points.length <= 2;
    remove.addEventListener("click", () => {
      renderWaypoints(readPoints().filter((_, i) => i !== index));
      markEdited();
    });
    row.append(remove);
    $("waypoints").append(row);
  });
  $("add-waypoint").disabled = points.length >= 20;
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status}).`);
  return payload;
}

function showError(message) {
  $("form-error").textContent = message;
  $("form-error").hidden = false;
}

function updatePosition() {
  if (!currentRun) return;
  const sample = currentRun.trajectory[Number($("timeline").value)];
  const [x, y] = project(sample);
  const marker = $("position-marker");
  marker.setAttribute("cx", x);
  marker.setAttribute("cy", y);
  $("time-label").textContent = `${sample.t_s.toFixed(1)} s`;
  $("altitude-label").textContent = `Z ${sample.z_m.toFixed(1)} m`;
}

function displayRun(run) {
  stopPlayback();
  currentRun = run;
  $("drone-name").value = run.mission.drone.name;
  $("mass").value = run.mission.drone.mass_kg;
  $("speed").value = run.mission.speed_mps;
  document.querySelectorAll('[name="sensor"]').forEach((input) => { input.checked = run.mission.drone.sensors.includes(input.value); });
  renderWaypoints(run.mission.waypoints);
  drawRoute(run.mission.waypoints);
  $("distance").textContent = run.metrics.planned_distance_m.toLocaleString(undefined, { maximumFractionDigits: 1 });
  $("duration").textContent = run.metrics.nominal_duration_s.toLocaleString(undefined, { maximumFractionDigits: 1 });
  $("point-count").textContent = run.metrics.waypoint_count;
  $("preview-state").textContent = "PREVIEW SAVED";
  $("preview-state").classList.add("complete");
  $("map-label").textContent = "Ideal path · no physics";
  $("run-label").textContent = `Run ${run.id.slice(0, 8)} · ${new Date(run.created_at).toLocaleString()}`;
  $("download").disabled = $("play").disabled = $("timeline").disabled = false;
  $("timeline").max = run.trajectory.length - 1;
  $("timeline").value = 0;
  $("form-error").hidden = true;
  updatePosition();
  if (busy) setBusy(true);
}

async function loadHistory() {
  try {
    const { runs } = await api("/api/runs");
    $("history").replaceChildren();
    $("history-status").textContent = runs.length ? "Latest 20 previews. Select a run to inspect its saved configuration." : "No previews yet. Your first run will appear here.";
    runs.forEach((run) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "history-row";
      const info = document.createElement("span"), name = document.createElement("strong"), detail = document.createElement("small"), distance = document.createElement("span");
      name.textContent = run.mission.drone.name;
      detail.textContent = `${new Date(run.created_at).toLocaleString()} · ${run.metrics.waypoint_count} points · preview`;
      distance.className = "history-distance";
      distance.textContent = `${run.metrics.planned_distance_m.toFixed(1)} m ↗`;
      info.append(name, detail);
      button.append(info, distance);
      button.addEventListener("click", async () => {
        if (busy) return;
        busy = true;
        setBusy(true);
        try { displayRun(await api(`/api/runs/${encodeURIComponent(run.id)}`)); }
        catch (error) { showError(error.message); }
        finally { busy = false; setBusy(false); }
      });
      $("history").append(button);
    });
  } catch (error) {
    $("history-status").textContent = `Could not load history: ${error.message}`;
  }
}

function setBusy(value) {
  // Prevent edits and history selection racing with a submitted configuration.
  $("mission-form").querySelectorAll("input, button").forEach((element) => { element.disabled = value; });
  $("run-button").textContent = value ? "Generating preview…" : "Generate preview ↗";
  if (!value) {
    $("add-waypoint").disabled = readPoints().length >= 20;
    document.querySelectorAll(".remove").forEach((button) => { button.disabled = readPoints().length <= 2; });
  }
}

$("mission-form").addEventListener("input", markEdited);
$("add-waypoint").addEventListener("click", () => {
  renderWaypoints([...readPoints(), { x_m: 0, y_m: 0, z_m: 10 }]);
  markEdited();
});
$("reset").addEventListener("click", () => { renderWaypoints(defaultPoints); markEdited(); });
$("mission-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  const mission = {
    drone: { name: $("drone-name").value.trim(), mass_kg: Number($("mass").value), sensors: [...document.querySelectorAll('[name="sensor"]:checked')].map((input) => input.value) },
    speed_mps: Number($("speed").value), waypoints: readPoints(),
  };
  busy = true;
  stopPlayback();
  setBusy(true);
  $("form-error").hidden = true;
  try {
    displayRun(await api("/api/missions", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(mission) }));
    await loadHistory();
  } catch (error) { showError(error.message); }
  finally { busy = false; setBusy(false); }
});
$("timeline").addEventListener("input", () => { stopPlayback(); updatePosition(); });
$("play").addEventListener("click", () => {
  if (!currentRun) return;
  if (animation !== null) { stopPlayback(); return; }
  if (Number($("timeline").value) >= Number($("timeline").max)) $("timeline").value = 0;
  const offset = Number($("timeline").value);
  let start;
  $("play").textContent = "Ⅱ";
  $("play").setAttribute("aria-label", "Pause preview");
  // Scrub the samples over eight seconds for inspection, independent of nominal duration.
  const tick = (time) => {
    if (start === undefined) start = time;
    const index = Math.min(Number($("timeline").max), offset + Math.floor((time - start) / 40));
    $("timeline").value = index;
    updatePosition();
    if (index < Number($("timeline").max)) animation = requestAnimationFrame(tick);
    else stopPlayback();
  };
  animation = requestAnimationFrame(tick);
});
$("download").addEventListener("click", () => {
  if (!currentRun) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(currentRun, null, 2)], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `autosim-${currentRun.id}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
$("refresh").addEventListener("click", loadHistory);
renderWaypoints(defaultPoints);
drawRoute(readPoints());
api("/api/health").then(() => { $("connection").textContent = "Local API connected"; }).catch(() => { $("connection").textContent = "API unavailable"; $("connection").classList.add("offline"); });
loadHistory();
