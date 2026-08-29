// Portfolio as a tiny top-down RPG. Hand-written tile engine, no libraries.
(function () {
  var dataEl = document.getElementById("world-data");
  var canvas = document.getElementById("stage");
  if (!dataEl || !canvas) return;

  var W = JSON.parse(dataEl.textContent);
  var ctx = canvas.getContext("2d");
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- palette ----
  var C = {
    grassA: "#3f7a34", grassB: "#45832f", water: "#2f6ea5", waterB: "#357ab3",
    trunk: "#5b3a1e", leaf: "#245b22", leafHi: "#2f7a2c",
    wall: "#d8c7a3", wallDark: "#b8a684", door: "#4a3320",
    skin: "#e8b892", hair: "#33241a", shirt: "#d1493b", pants: "#3c4c7a",
    padA: "#caa64a", padB: "#e6c56a", text: "#f4ecd8", shadow: "rgba(0,0,0,.28)",
  };

  // ---- collision + interaction maps ----
  var solid = new Set();
  var mats = new Map();
  for (var y = 0; y < W.rows; y++) {
    for (var x = 0; x < W.cols; x++) {
      var t = W.terrain[y][x];
      if (t === "T" || t === "~") solid.add(x + "," + y);
    }
  }
  W.trees.forEach(function (p) { solid.add(p[0] + "," + p[1]); });
  W.structures.forEach(function (s) {
    solid.add(s.x + "," + s.y);
    mats.set(s.x + "," + (s.y + 1), s);
  });
  mats.set(W.pad.x + "," + W.pad.y, W.pad);

  function walkable(x, y) {
    return x >= 0 && y >= 0 && x < W.cols && y < W.rows && !solid.has(x + "," + y);
  }

  // ---- player ----
  var P = { tx: W.start.x, ty: W.start.y, fx: W.start.x, fy: W.start.y, dir: "down", moving: false, frame: 0, tick: 0 };
  var keys = {};
  var queue = null; // one-shot direction from a tap
  var started = false;

  var DELTA = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] };
  function tryStep() {
    if (P.moving) return;
    var dir = keys.up ? "up" : keys.down ? "down" : keys.left ? "left" : keys.right ? "right" : queue;
    queue = null;
    if (!dir) return;
    P.dir = dir;
    var nx = P.tx + DELTA[dir][0], ny = P.ty + DELTA[dir][1];
    if (walkable(nx, ny)) { P.tx = nx; P.ty = ny; P.moving = true; }
  }

  var quest = document.getElementById("quest");
  var questBody = document.getElementById("quest-body");
  document.getElementById("quest-close").addEventListener("click", closeQuest);
  function closeQuest() { quest.hidden = true; }

  function tryEnter() {
    if (!quest.hidden) { closeQuest(); return; }
    var m = mats.get(P.tx + "," + P.ty);
    if (m) openQuest(m.detail, m.name);
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function openQuest(d, name) {
    var h = '<p class="qkind">' + esc(d.kind) + "</p>";
    h += "<h3>" + esc(d.title) + (d.team ? ' <span class="pill">party</span>' : "") + "</h3>";
    if (d.body) h += "<p>" + esc(d.body) + "</p>";
    if (d.meta) h += '<p class="qmeta">' + esc(d.meta) + "</p>";
    if (d.stats) {
      h += '<div class="bars">';
      d.stats.forEach(function (s) {
        h += '<div class="bar"><span>' + esc(s[0]) + '</span><i style="--v:' + s[1] + '"></i><b>' + s[1] + "</b></div>";
      });
      h += "</div>";
    }
    if (d.objectives && d.objectives.length) {
      h += '<p class="qlabel">— objectives —</p><ul>';
      d.objectives.forEach(function (o) { h += "<li>" + esc(o) + "</li>"; });
      h += "</ul>";
    }
    if (d.loot && d.loot.length) {
      h += '<p class="qlabel">— loot —</p><div class="chips">';
      d.loot.forEach(function (l) { h += '<span class="chip">' + esc(l) + "</span>"; });
      h += "</div>";
    }
    if (d.link) h += '<a class="qlink" href="' + esc(d.link) + '" target="_blank" rel="noopener">' + esc(d.link_label || "open →") + "</a>";
    if (d.links) Object.keys(d.links).forEach(function (k) {
      h += '<a class="qlink" href="' + esc(d.links[k]) + '" target="_blank" rel="noopener">' + esc(k) + " →</a>";
    });
    questBody.innerHTML = h;
    quest.hidden = false;
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
    var set = function (v) {
      return function (e) {
        e.preventDefault();
        dismissTitle();
        if (k === "act") { if (v) tryEnter(); return; }
        keys[k] = v;
        if (v) queue = k;
      };
    };
    b.addEventListener("pointerdown", set(true));
    b.addEventListener("pointerup", set(false));
    b.addEventListener("pointerleave", set(false));
    b.addEventListener("pointercancel", set(false));
  });

  var titlecard = document.getElementById("titlecard");
  function dismissTitle() {
    if (started) return;
    started = true;
    titlecard.classList.add("gone");
  }
  if (reduced) dismissTitle();
  else setTimeout(dismissTitle, 2600);

  // ---- sizing ----
  var TS = 32;
  function resize() {
    var availW = canvas.parentElement.clientWidth;
    var availH = window.innerHeight - 56;
    TS = Math.max(14, Math.floor(Math.min(availW / W.cols, availH / W.rows)));
    canvas.width = TS * W.cols;
    canvas.height = TS * W.rows;
  }
  window.addEventListener("resize", resize);
  window.addEventListener("viewchange", resize);
  resize();

  // ---- draw helpers ----
  function px(v) { return Math.round(v); }
  function rect(x, y, w, h, col) { ctx.fillStyle = col; ctx.fillRect(px(x), px(y), Math.ceil(w), Math.ceil(h)); }

  function drawTree(cx, cy) {
    rect(cx + TS * 0.42, cy + TS * 0.5, TS * 0.16, TS * 0.4, C.trunk);
    rect(cx + TS * 0.15, cy + TS * 0.12, TS * 0.7, TS * 0.5, C.leaf);
    rect(cx + TS * 0.24, cy + TS * 0.04, TS * 0.52, TS * 0.3, C.leafHi);
  }
  function drawHouse(cx, cy, roof) {
    rect(cx + TS * 0.08, cy + TS * 0.42, TS * 0.84, TS * 0.56, C.wall);
    rect(cx + TS * 0.08, cy + TS * 0.42, TS * 0.84, TS * 0.1, C.wallDark);
    // roof
    ctx.fillStyle = roof;
    ctx.beginPath();
    ctx.moveTo(px(cx), px(cy + TS * 0.46));
    ctx.lineTo(px(cx + TS / 2), px(cy + TS * 0.06));
    ctx.lineTo(px(cx + TS), px(cy + TS * 0.46));
    ctx.closePath();
    ctx.fill();
    rect(cx + TS * 0.4, cy + TS * 0.62, TS * 0.2, TS * 0.36, C.door);
  }
  function drawPad(cx, cy, glow) {
    rect(cx + 1, cy + 1, TS - 2, TS - 2, glow ? C.padB : C.padA);
    rect(cx + TS * 0.2, cy + TS * 0.2, TS * 0.6, TS * 0.6, glow ? C.padA : C.padB);
  }
  function drawPlayer(cx, cy) {
    rect(cx + TS * 0.24, cy + TS * 0.82, TS * 0.52, TS * 0.14, C.shadow);
    var bob = P.moving && (P.frame % 20 < 10) ? 1 : 0;
    rect(cx + TS * 0.3, cy + TS * 0.62 - bob, TS * 0.16, TS * 0.2, C.pants);
    rect(cx + TS * 0.54, cy + TS * 0.62 + bob, TS * 0.16, TS * 0.2, C.pants);
    rect(cx + TS * 0.28, cy + TS * 0.36, TS * 0.44, TS * 0.3, C.shirt);
    rect(cx + TS * 0.3, cy + TS * 0.1, TS * 0.4, TS * 0.3, C.skin);
    rect(cx + TS * 0.28, cy + TS * 0.06, TS * 0.44, TS * 0.12, C.hair);
    ctx.fillStyle = "#20140c";
    if (P.dir === "down") { rect(cx + TS * 0.38, cy + TS * 0.24, TS * 0.06, TS * 0.06, "#20140c"); rect(cx + TS * 0.56, cy + TS * 0.24, TS * 0.06, TS * 0.06, "#20140c"); }
    else if (P.dir === "left") rect(cx + TS * 0.36, cy + TS * 0.24, TS * 0.06, TS * 0.06, "#20140c");
    else if (P.dir === "right") rect(cx + TS * 0.58, cy + TS * 0.24, TS * 0.06, TS * 0.06, "#20140c");
    else rect(cx + TS * 0.3, cy + TS * 0.08, TS * 0.4, TS * 0.16, C.hair);
  }

  // ---- loop ----
  function frame() {
    P.tick++;
    if (!started) { requestAnimationFrame(frame); draw(); return; }

    tryStep();
    if (P.moving) {
      P.frame++;
      var sp = 0.16;
      P.fx += Math.sign(P.tx - P.fx) * Math.min(sp, Math.abs(P.tx - P.fx));
      P.fy += Math.sign(P.ty - P.fy) * Math.min(sp, Math.abs(P.ty - P.fy));
      if (Math.abs(P.fx - P.tx) < 0.01 && Math.abs(P.fy - P.ty) < 0.01) {
        P.fx = P.tx; P.fy = P.ty; P.moving = false;
      }
    }
    draw();
    requestAnimationFrame(frame);
  }

  function draw() {
    // ground
    for (var y = 0; y < W.rows; y++) {
      for (var x = 0; x < W.cols; x++) {
        var t = W.terrain[y][x];
        var base = (x + y) % 2 ? C.grassA : C.grassB;
        if (t === "~") base = ((x + y + (P.tick >> 5)) % 2) ? C.water : C.waterB;
        rect(x * TS, y * TS, TS, TS, base);
      }
    }
    // structures + labels
    W.structures.forEach(function (s) {
      drawHouse(s.x * TS, s.y * TS, s.roof);
      ctx.fillStyle = C.text;
      ctx.font = Math.max(9, TS * 0.3) + "px 'VT323', monospace";
      ctx.textAlign = "center";
      ctx.fillText(s.name, s.x * TS + TS / 2, s.y * TS - TS * 0.12);
    });
    drawPad(W.pad.x * TS, W.pad.y * TS, (P.tick >> 4) % 2 === 0);
    ctx.fillStyle = C.text;
    ctx.font = Math.max(9, TS * 0.3) + "px 'VT323', monospace";
    ctx.textAlign = "center";
    ctx.fillText("Skill tree", W.pad.x * TS + TS / 2, W.pad.y * TS - TS * 0.12);
    // trees
    W.trees.forEach(function (p) { drawTree(p[0] * TS, p[1] * TS); });
    // player
    drawPlayer(P.fx * TS, P.fy * TS);
    // prompt
    var m = mats.get(P.tx + "," + P.ty);
    var hud = document.getElementById("prompt");
    if (m && quest.hidden) {
      if (!hud) {
        hud = document.createElement("div");
        hud.id = "prompt";
        hud.className = "vt";
        document.getElementById("game").appendChild(hud);
      }
      hud.textContent = "▸ press E — enter " + (m.name || m.detail.title);
      hud.style.display = "block";
    } else if (hud) {
      hud.style.display = "none";
    }
  }

  requestAnimationFrame(frame);
})();
