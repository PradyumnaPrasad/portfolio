// Portfolio as a cozy top-down RPG. Hand-written tile engine + WebAudio blips.
(function () {
  var dataEl = document.getElementById("world-data");
  var canvas = document.getElementById("stage");
  if (!dataEl || !canvas) return;

  var W = JSON.parse(dataEl.textContent);
  var ctx = canvas.getContext("2d");
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var COL = {
    grass1: "#5aa04a", grass2: "#65ac52", tuft: "#4c9040", flower1: "#f0d24a", flower2: "#e98ab0",
    path: "#caa877", pathHi: "#dbbd8e", pathLo: "#a9895d",
    water1: "#3f8fce", water2: "#4fa0da", foam: "#bfe6f5",
    trunk: "#6b4326", leaf1: "#2f7d3a", leaf2: "#3c9247", leafHi: "#57ab5c", leafLo: "#255f2d",
    wall: "#e8d7b0", wallLo: "#d3bf95", plank: "#d8c49c",
    win: "#8fd0e0", winLit: "#ffe08a", door: "#7a4a28", doorFr: "#5c3418",
    ridge: "#00000022", eave: "#00000033", chim: "#8a6b52", smoke: "#ffffffcc",
    signBoard: "#b07d47", signPost: "#7c5330", signInk: "#3a2414",
    skin: "#f0c199", hair: "#3a2a1c", shirt: "#d24b3c", shirtLo: "#b23a2d", pants: "#3d4a78", boot: "#5b3a22",
    rune: "#7c7566", runeGlow: "#8be0c8",
    ink: "#f4ecd8", shadow: "rgba(20,24,16,.24)",
  };

  // ---- world maps ----
  var solid = new Set(), path = new Set(), mats = new Map(), land = new Set();
  for (var y = 0; y < W.rows; y++) for (var x = 0; x < W.cols; x++) {
    var t = W.terrain[y][x];
    if (t === "T" || t === "~") solid.add(x + "," + y); else land.add(x + "," + y);
  }
  W.paths.forEach(function (p) { path.add(p[0] + "," + p[1]); });
  W.trees.forEach(function (p) { solid.add(p[0] + "," + p[1]); });
  W.structures.forEach(function (s) { solid.add(s.x + "," + s.y); mats.set(s.x + "," + (s.y + 1), s); });
  mats.set(W.pad.x + "," + W.pad.y, W.pad);
  function walkable(x, y) { return x >= 0 && y >= 0 && x < W.cols && y < W.rows && !solid.has(x + "," + y); }
  function hash(x, y) { var n = (x * 73856093) ^ (y * 19349663); n = (n ^ (n >> 13)) >>> 0; return n / 4294967295; }

  // ---- audio ----
  var actx = null, sfxOn = false;
  try { sfxOn = localStorage.getItem("sfx") === "1"; } catch (e) {}
  function beep(freq, dur, type, vol) {
    if (!sfxOn) return;
    if (!actx) { try { actx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { return; } }
    var o = actx.createOscillator(), g = actx.createGain();
    o.type = type || "square"; o.frequency.value = freq;
    g.gain.value = vol == null ? 0.05 : vol;
    o.connect(g); g.connect(actx.destination);
    var now = actx.currentTime;
    g.gain.setValueAtTime(g.gain.value, now);
    g.gain.exponentialRampToValueAtTime(0.0001, now + dur);
    o.start(now); o.stop(now + dur);
  }
  var SFX = {
    step: function () { beep(150 + Math.random() * 20, 0.06, "square", 0.03); },
    bump: function () { beep(90, 0.09, "sawtooth", 0.035); },
    enter: function () { beep(440, 0.08, "square", 0.05); setTimeout(function () { beep(660, 0.12, "square", 0.05); }, 80); },
    close: function () { beep(330, 0.07, "square", 0.04); },
  };
  var spk = document.getElementById("speaker");
  function paintSpeaker() { if (spk) spk.textContent = sfxOn ? "♪ on" : "♪ off"; }
  if (spk) spk.addEventListener("click", function () {
    sfxOn = !sfxOn;
    try { localStorage.setItem("sfx", sfxOn ? "1" : "0"); } catch (e) {}
    paintSpeaker();
    if (sfxOn) SFX.enter();
  });
  paintSpeaker();

  // ---- player ----
  var P = { tx: W.start.x, ty: W.start.y, fx: W.start.x, fy: W.start.y, dir: "down", moving: false, anim: 0, bumpCd: 0 };
  var keys = {}, queue = null, started = false;
  var DELTA = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] };

  function tryStep() {
    if (P.moving) return;
    var dir = keys.up ? "up" : keys.down ? "down" : keys.left ? "left" : keys.right ? "right" : queue;
    queue = null;
    if (!dir) return;
    P.dir = dir;
    var nx = P.tx + DELTA[dir][0], ny = P.ty + DELTA[dir][1];
    if (walkable(nx, ny)) { P.tx = nx; P.ty = ny; P.moving = true; SFX.step(); }
    else if (P.bumpCd <= 0) { SFX.bump(); P.bumpCd = 18; }
  }

  // ---- quest panel ----
  var quest = document.getElementById("quest"), questBody = document.getElementById("quest-body");
  document.getElementById("quest-close").addEventListener("click", closeQuest);
  function closeQuest() { if (quest.hidden) return; quest.hidden = true; quest.classList.remove("in"); SFX.close(); }
  function tryEnter() {
    if (!quest.hidden) { closeQuest(); return; }
    var m = mats.get(P.tx + "," + P.ty);
    if (m) { openQuest(m.detail, m.icon); SFX.enter(); }
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  var ICON = { home: "⌂", guild: "⚑", mail: "✉", trophy: "♛", hammer: "⚒", house: "▤", telescope: "✦" };
  function openQuest(d, icon) {
    var h = '<p class="qkind"><span class="qicon">' + (ICON[icon] || "◆") + "</span>" + esc(d.kind) + "</p>";
    h += "<h3>" + esc(d.title) + (d.team ? ' <span class="pill">party</span>' : "") + "</h3>";
    if (d.body) h += "<p>" + esc(d.body) + "</p>";
    if (d.meta) h += '<p class="qmeta">' + esc(d.meta) + "</p>";
    if (d.stats) {
      h += '<div class="bars">';
      d.stats.forEach(function (s) { h += '<div class="bar"><span>' + esc(s[0]) + '</span><i style="--v:' + s[1] + '"></i><b>' + s[1] + "</b></div>"; });
      h += "</div>";
    }
    if (d.objectives && d.objectives.length) {
      h += '<p class="qlabel">objectives</p><ul>';
      d.objectives.forEach(function (o) { h += "<li>" + esc(o) + "</li>"; });
      h += "</ul>";
    }
    if (d.loot && d.loot.length) {
      h += '<p class="qlabel">loot</p><div class="chips">';
      d.loot.forEach(function (l) { h += '<span class="chip">' + esc(l) + "</span>"; });
      h += "</div>";
    }
    var links = [];
    if (d.link) {
      var internal = d.link.charAt(0) === "/";
      var tgt = internal ? "" : ' target="_blank" rel="noopener"';
      links.push('<a class="qlink" href="' + esc(d.link) + '"' + tgt + ">" + esc(d.link_label || "open →") + "</a>");
    }
    if (d.links) Object.keys(d.links).forEach(function (k) { links.push('<a class="qlink" href="' + esc(d.links[k]) + '" target="_blank" rel="noopener">' + esc(k) + " →</a>"); });
    if (links.length) h += '<div class="qlinks">' + links.join("") + "</div>";
    h += '<p class="qfoot">press <b>E</b> or <b>Esc</b> to close</p>';
    questBody.innerHTML = h;
    quest.hidden = false;
    requestAnimationFrame(function () { quest.classList.add("in"); });
  }

  // ---- input ----
  var KMAP = { ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right", w: "up", s: "down", a: "left", d: "right", W: "up", S: "down", A: "left", D: "right" };
  window.addEventListener("keydown", function (e) {
    if (document.documentElement.classList.contains("text")) return;
    dismissTitle();
    if (KMAP[e.key]) { keys[KMAP[e.key]] = true; queue = KMAP[e.key]; e.preventDefault(); }
    else if (e.key === "e" || e.key === "E" || e.key === " " || e.key === "Enter") { tryEnter(); e.preventDefault(); }
    else if (e.key === "Escape") closeQuest();
  });
  window.addEventListener("keyup", function (e) { if (KMAP[e.key]) keys[KMAP[e.key]] = false; });
  document.querySelectorAll("#dpad button").forEach(function (b) {
    var k = b.dataset.k;
    function set(v) { return function (e) { e.preventDefault(); dismissTitle(); if (k === "act") { if (v) tryEnter(); return; } keys[k] = v; if (v) queue = k; }; }
    b.addEventListener("pointerdown", set(true));
    b.addEventListener("pointerup", set(false));
    b.addEventListener("pointerleave", set(false));
    b.addEventListener("pointercancel", set(false));
  });
  var titlecard = document.getElementById("titlecard");
  function dismissTitle() { if (started) return; started = true; titlecard.classList.add("gone"); }
  if (reduced) dismissTitle(); else setTimeout(dismissTitle, 3200);

  // ---- sizing + camera ----
  var TS = 32, U;
  var cam = { x: 0, y: 0 };
  var gameEl = document.getElementById("game");
  function resize() {
    var availW = gameEl.clientWidth - 28;
    var availH = window.innerHeight - 56 - 90;
    var mapW = availW / W.cols, mapH = availH / W.rows;
    if (Math.min(mapW, mapH) >= 20) {
      // whole map fits comfortably — show all of it
      TS = Math.min(52, Math.floor(Math.min(mapW, mapH)));
    } else {
      // small screen — zoom in and let the camera follow the player
      TS = Math.max(22, Math.min(40, Math.floor(Math.min(availW, availH) / 9)));
    }
    U = TS / 16;
    canvas.width = Math.min(TS * W.cols, Math.floor(availW));
    canvas.height = Math.min(TS * W.rows, Math.floor(availH));
  }
  function updateCamera() {
    var maxX = TS * W.cols - canvas.width;
    var maxY = TS * W.rows - canvas.height;
    var tx = maxX <= 0 ? maxX / 2 : clamp((P.fx + 0.5) * TS - canvas.width / 2, 0, maxX);
    var ty = maxY <= 0 ? maxY / 2 : clamp((P.fy + 0.5) * TS - canvas.height / 2, 0, maxY);
    cam.x += (tx - cam.x) * 0.2;
    cam.y += (ty - cam.y) * 0.2;
  }
  function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }
  window.addEventListener("resize", resize);
  window.addEventListener("viewchange", resize);
  resize();

  // ---- draw helpers (r in 1/16-tile units) ----
  function box(tx, ty, rx, ry, rw, rh, col) {
    ctx.fillStyle = col;
    ctx.fillRect(Math.round(tx * TS + rx * U), Math.round(ty * TS + ry * U), Math.ceil(rw * U), Math.ceil(rh * U));
  }
  function px(sx, sy, w, h, col) { ctx.fillStyle = col; ctx.fillRect(Math.round(sx), Math.round(sy), Math.ceil(w), Math.ceil(h)); }

  function drawGround() {
    for (var y = 0; y < W.rows; y++) for (var x = 0; x < W.cols; x++) {
      var key = x + "," + y, t = W.terrain[y][x];
      if (t === "~") {
        var f = ((x * 2 + y + (frameCt >> 4)) % 5 === 0);
        box(x, y, 0, 0, 16, 16, f ? COL.water2 : COL.water1);
        if (land.has(x + "," + (y + 1))) box(x, y, 0, 12, 16, 3, COL.foam);
        if (land.has(x + "," + (y - 1))) box(x, y, 0, 1, 16, 2, COL.foam);
        continue;
      }
      box(x, y, 0, 0, 16, 16, (x + y) % 2 ? COL.grass1 : COL.grass2);
      if (t === "T") { continue; }
      if (path.has(key)) {
        box(x, y, 1, 1, 14, 14, COL.path);
        if (!path.has(x + "," + (y - 1))) box(x, y, 1, 1, 14, 2, COL.pathHi);
        if (!path.has((x - 1) + "," + y)) box(x, y, 1, 1, 2, 14, COL.pathHi);
        if (!path.has(x + "," + (y + 1))) box(x, y, 1, 13, 14, 2, COL.pathLo);
        var h2 = hash(x + 40, y);
        if (h2 > 0.7) box(x, y, 3 + (h2 * 8 | 0), 4 + (h2 * 6 | 0), 2, 2, COL.pathLo);
      } else {
        var h = hash(x, y);
        if (h > 0.86) { box(x, y, 3, 9, 3, 2, COL.tuft); box(x, y, 10, 4, 2, 2, COL.tuft); }
        else if (h < 0.05 && !mats.has(key)) box(x, y, 6 + (h * 60 | 0) % 4, 6, 2, 2, h < 0.025 ? COL.flower1 : COL.flower2);
      }
    }
  }

  function drawTree(x, y) {
    var v = hash(x, y) > 0.5 ? 0 : 1;
    box(x, y, 3, 13, 12, 3, COL.shadow);
    box(x, y, 7, 8, 3, 7, COL.trunk);
    var s = v ? 0.5 : 0;
    box(x, y, 1, 2 - s, 14, 9, COL.leaf1);
    box(x, y, 3, 0 - s, 10, 8, COL.leaf2);
    box(x, y, 4, 1 - s, 6, 4, COL.leafHi);
    box(x, y, 2, 9, 12, 2, COL.leafLo);
  }

  function drawHouse(s) {
    var x = s.x, y = s.y;
    box(x, y, -2, 15, 20, 3, COL.shadow);
    // walls
    box(x, y - 1, 0, 6, 16, 11, COL.wall);
    box(x, y - 1, 0, 6, 16, 2, COL.wallLo);
    for (var i = 8; i < 17; i += 3) box(x, y - 1, 0, i, 16, 1, COL.plank);
    // window
    box(x, y - 1, 2.5, 9, 3.6, 3.6, COL.doorFr);
    box(x, y - 1, 3, 9.5, 2.6, 2.6, COL.winLit);
    box(x, y - 1, 4.2, 9.5, 0.4, 2.6, COL.doorFr);
    box(x, y - 1, 3, 10.6, 2.6, 0.4, COL.doorFr);
    // door
    box(x, y - 1, 9.8, 8, 4.4, 9, COL.doorFr);
    box(x, y - 1, 10.4, 8.6, 3.2, 8.4, COL.door);
    box(x, y - 1, 12.6, 12.3, 0.9, 0.9, "#e8c05a");
    // roof
    ctx.fillStyle = s.roof;
    ctx.beginPath();
    ctx.moveTo(Math.round((x - 0.15) * TS), Math.round((y - 1) * TS + 7 * U));
    ctx.lineTo(Math.round((x + 0.5) * TS), Math.round((y - 1) * TS - 4 * U));
    ctx.lineTo(Math.round((x + 1.15) * TS), Math.round((y - 1) * TS + 7 * U));
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = COL.eave;
    ctx.fillRect(Math.round((x - 0.15) * TS), Math.round((y - 1) * TS + 5.5 * U), Math.ceil(1.3 * TS), Math.ceil(1.6 * U));
    box(x, y - 1, 6, -3, 4, 2, "#ffffff33");
    // chimney + smoke
    box(x, y - 1, 11, -2, 2.5, 5, COL.chim);
    if (!reduced) {
      var pf = (frameCt / 24) % 1;
      for (var p = 0; p < 3; p++) {
        var t2 = (pf + p / 3) % 1;
        box(x, y - 1, 11.5 + Math.sin(t2 * 6 + x) * 1.5, -3 - t2 * 8, 2 - t2, 2 - t2, "rgba(255,255,255," + (0.5 * (1 - t2)).toFixed(2) + ")");
      }
    }
    drawSign(x, y, s.name);
  }

  function drawSign(x, y, text) {
    var cx = (x + 0.5) * TS, top = (y - 1) * TS - 6 * U;
    ctx.font = "bold " + Math.max(9, Math.round(TS * 0.34)) + "px 'VT323', monospace";
    ctx.textAlign = "center";
    var w = ctx.measureText(text).width + 10 * U;
    px(cx - w / 2, top, w, 9 * U, COL.signPost);
    px(cx - w / 2 + 1, top + 1, w - 2, 7 * U, COL.signBoard);
    ctx.fillStyle = COL.signInk;
    ctx.textBaseline = "middle";
    ctx.fillText(text, cx, top + 4.5 * U);
    ctx.textBaseline = "alphabetic";
  }

  function drawRune(x, y) {
    box(x, y, 1, 1, 14, 14, "#5c574c");
    box(x, y, 2, 2, 12, 12, COL.rune);
    var g = 0.4 + 0.3 * Math.sin(frameCt / 18);
    ctx.strokeStyle = "rgba(139,224,200," + g.toFixed(2) + ")";
    ctx.lineWidth = Math.max(1, 1.4 * U);
    ctx.beginPath();
    ctx.arc((x + 0.5) * TS, (y + 0.5) * TS, 4.5 * U, 0, Math.PI * 2);
    ctx.stroke();
    box(x, y, 7.2, 3, 1.6, 10, "rgba(139,224,200," + g.toFixed(2) + ")");
    box(x, y, 3, 7.2, 10, 1.6, "rgba(139,224,200," + g.toFixed(2) + ")");
    drawSign(x, y + 1, "Skill Tree");
  }

  function drawPlayer() {
    var x = P.fx, y = P.fy;
    var walk = P.moving ? (Math.floor(P.anim / 6) % 4) : 0;
    var lift = walk === 1 ? -1 : walk === 3 ? 1 : 0;
    var bob = P.moving ? (walk % 2 ? 0.4 : 0) : Math.sin(frameCt / 40) * 0.3;
    box(x, y, 3, 13.5, 10, 2.5, COL.shadow);
    // legs
    box(x, y, 5.5, 11 - bob + Math.max(0, lift), 2, 3, COL.pants);
    box(x, y, 8.5, 11 - bob - Math.max(0, -lift), 2, 3, COL.pants);
    box(x, y, 5.5, 13.5, 2, 1, COL.boot);
    box(x, y, 8.5, 13.5, 2, 1, COL.boot);
    // body
    box(x, y, 4.5, 6.5 - bob, 7, 5, COL.shirt);
    box(x, y, 4.5, 9.5 - bob, 7, 1, COL.shirtLo);
    // head
    box(x, y, 4.5, 1.5 - bob, 7, 5.5, COL.skin);
    box(x, y, 4, 0.5 - bob, 8, 2.5, COL.hair);
    if (P.dir === "down") { box(x, y, 6, 4 - bob, 1.2, 1.2, COL.hair); box(x, y, 8.8, 4 - bob, 1.2, 1.2, COL.hair); }
    else if (P.dir === "up") { box(x, y, 4, 1 - bob, 8, 3.5, COL.hair); }
    else if (P.dir === "left") { box(x, y, 5, 4 - bob, 1.2, 1.2, COL.hair); box(x, y, 4, 2 - bob, 1.5, 4, COL.hair); }
    else { box(x, y, 9.8, 4 - bob, 1.2, 1.2, COL.hair); box(x, y, 10.5, 2 - bob, 1.5, 4, COL.hair); }
  }

  function drawBubble() {
    var m = mats.get(P.tx + "," + P.ty);
    if (!m || !quest.hidden || !started) return;
    var cx = (P.fx + 0.5) * TS, by = (P.fy - 0.35) * TS;
    var label = "Enter · " + (m.name || m.detail.title);
    ctx.font = "bold " + Math.max(10, Math.round(TS * 0.32)) + "px 'VT323', monospace";
    ctx.textAlign = "left";
    var pad = 6 * U, kw = 12 * U;
    var w = kw + 4 * U + ctx.measureText(label).width + pad * 2;
    var h = 15 * U, bx = cx - w / 2;
    var yy = by - h - 3 * U + Math.sin(frameCt / 20) * 1.5;
    px(bx, yy, w, h, "#1c2016");
    px(bx + 1, yy + 1, w - 2, h - 2, "#f4ecd8");
    ctx.beginPath();
    ctx.fillStyle = "#f4ecd8";
    ctx.moveTo(cx - 4 * U, yy + h); ctx.lineTo(cx + 4 * U, yy + h); ctx.lineTo(cx, yy + h + 5 * U);
    ctx.closePath(); ctx.fill();
    px(bx + pad, yy + (h - kw) / 2, kw, kw, "#1c2016");
    ctx.fillStyle = "#ffe08a";
    ctx.textBaseline = "middle";
    ctx.fillText("E", bx + pad + 3 * U, yy + h / 2 + 0.5 * U);
    ctx.fillStyle = "#3a2414";
    ctx.fillText(label, bx + pad + kw + 4 * U, yy + h / 2 + 0.5 * U);
    ctx.textBaseline = "alphabetic";
  }

  function drawVignette() {
    var g = ctx.createRadialGradient(canvas.width / 2, canvas.height / 2, canvas.height * 0.3, canvas.width / 2, canvas.height / 2, canvas.height * 0.8);
    g.addColorStop(0, "rgba(0,0,0,0)");
    g.addColorStop(1, "rgba(10,14,8,0.35)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  // ---- loop ----
  var frameCt = 0;
  function frame() {
    frameCt++;
    if (started) {
      if (P.bumpCd > 0) P.bumpCd--;
      tryStep();
      if (P.moving) {
        P.anim++;
        var sp = 0.14;
        P.fx += Math.sign(P.tx - P.fx) * Math.min(sp, Math.abs(P.tx - P.fx));
        P.fy += Math.sign(P.ty - P.fy) * Math.min(sp, Math.abs(P.ty - P.fy));
        if (Math.abs(P.fx - P.tx) < 0.02 && Math.abs(P.fy - P.ty) < 0.02) { P.fx = P.tx; P.fy = P.ty; P.moving = false; }
      } else P.anim = 0;
    }
    updateCamera();
    draw();
    requestAnimationFrame(frame);
  }

  function draw() {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.translate(-Math.round(cam.x), -Math.round(cam.y));
    drawGround();
    var sprites = [];
    W.structures.forEach(function (s) { sprites.push({ z: s.y + 1, fn: function () { drawHouse(s); } }); });
    W.trees.forEach(function (p) { sprites.push({ z: p[1] + 1, fn: function () { drawTree(p[0], p[1]); } }); });
    sprites.push({ z: W.pad.y + 0.9, fn: function () { drawRune(W.pad.x, W.pad.y); } });
    sprites.push({ z: P.fy + 1, fn: drawPlayer });
    sprites.sort(function (a, b) { return a.z - b.z; });
    sprites.forEach(function (s) { s.fn(); });
    drawBubble();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    drawVignette();
  }

  requestAnimationFrame(frame);
})();
