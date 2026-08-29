// Hand-written force-directed graph on canvas. No libraries.
// Repulsion (O(n^2), fine for ~50 nodes) + edge springs + centering, then
// semi-implicit Euler integration. Camera supports pan + wheel zoom.
(function () {
  var dataEl = document.getElementById("graph-data");
  var canvas = document.getElementById("graph");
  if (!dataEl || !canvas) return;

  var raw = JSON.parse(dataEl.textContent);
  var ctx = canvas.getContext("2d");
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var SPEC = {
    person: { r: 15, mass: 8 },
    project: { r: 10, mass: 3 },
    experience: { r: 10, mass: 3 },
    achievement: { r: 8, mass: 2 },
    tech: { r: 6, mass: 1.4 },
  };
  function css(v) {
    return getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  }
  function colorFor(type) {
    return css("--node-" + type) || css("--text");
  }

  // ---- build model ----
  var byId = {};
  var nodes = raw.nodes.map(function (n) {
    var s = SPEC[n.type] || SPEC.tech;
    var node = {
      id: n.id, label: n.label, type: n.type, detail: n.detail || null,
      r: s.r, mass: s.mass,
      x: (Math.random() - 0.5) * 40, y: (Math.random() - 0.5) * 40,
      vx: 0, vy: 0,
    };
    byId[n.id] = node;
    return node;
  });
  if (byId.me) { byId.me.pinned = true; byId.me.x = 0; byId.me.y = 0; }

  var edges = raw.edges
    .map(function (e) {
      var s = byId[e.source], t = byId[e.target];
      if (!s || !t) return null;
      var anchored = s.type === "person" || t.type === "person";
      return { s: s, t: t, kind: e.kind, rest: anchored ? 170 : 58 };
    })
    .filter(Boolean);

  // neighbour + tech-usage maps
  var neighbours = {};
  nodes.forEach(function (n) { neighbours[n.id] = new Set(); });
  var techUse = {};
  edges.forEach(function (e) {
    neighbours[e.s.id].add(e.t.id);
    neighbours[e.t.id].add(e.s.id);
    if (e.t.type === "tech") (techUse[e.t.id] = techUse[e.t.id] || []).push(e.s.label);
  });

  // ---- camera ----
  var cam = { x: 0, y: 0, scale: 1 };
  var W = 0, H = 0, dpr = 1;
  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = canvas.clientWidth;
    H = canvas.clientHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
  }
  function toWorld(px, py) {
    return { x: (px - cam.x) / cam.scale, y: (py - cam.y) / cam.scale };
  }
  function fit(lerp) {
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach(function (n) {
      minX = Math.min(minX, n.x - n.r); maxX = Math.max(maxX, n.x + n.r);
      minY = Math.min(minY, n.y - n.r); maxY = Math.max(maxY, n.y + n.r);
    });
    var padX = Math.max(120, W * 0.06), padY = Math.max(80, H * 0.1);
    var sx = W / (maxX - minX + padX * 2);
    var sy = H / (maxY - minY + padY * 2);
    var s = Math.max(0.3, Math.min(2.2, Math.min(sx, sy) * 0.96));
    // keep the cloud clear of the top-left hero text
    var focalX = W > 900 ? W * 0.6 : W * 0.5;
    var focalY = W > 640 ? H * 0.5 : H * 0.62;
    var tx = focalX - ((minX + maxX) / 2) * s;
    var ty = focalY - ((minY + maxY) / 2) * s;
    var k = lerp || 1;
    cam.scale += (s - cam.scale) * k;
    cam.x += (tx - cam.x) * k;
    cam.y += (ty - cam.y) * k;
  }

  // ---- physics ----
  var SPRING = 0.018, REPULSION = 4200, CENTER = 0.0022, DAMP = 0.9;
  var settleFrames = 0;
  function step() {
    for (var i = 0; i < nodes.length; i++) {
      var a = nodes[i];
      for (var j = i + 1; j < nodes.length; j++) {
        var b = nodes[j];
        var dx = a.x - b.x, dy = a.y - b.y;
        var d2 = dx * dx + dy * dy || 0.01;
        var d = Math.sqrt(d2);
        var f = REPULSION / d2;
        var fx = (dx / d) * f, fy = (dy / d) * f;
        a.vx += fx / a.mass; a.vy += fy / a.mass;
        b.vx -= fx / b.mass; b.vy -= fy / b.mass;
      }
      a.vx -= a.x * CENTER;
      a.vy -= a.y * CENTER;
    }
    edges.forEach(function (e) {
      var dx = e.t.x - e.s.x, dy = e.t.y - e.s.y;
      var d = Math.sqrt(dx * dx + dy * dy) || 0.01;
      var f = SPRING * (d - e.rest);
      var fx = (dx / d) * f, fy = (dy / d) * f;
      e.s.vx += fx / e.s.mass; e.s.vy += fy / e.s.mass;
      e.t.vx -= fx / e.t.mass; e.t.vy -= fy / e.t.mass;
    });
    nodes.forEach(function (n) {
      if (n === dragging || n.pinned) { n.vx = n.vy = 0; return; }
      n.vx *= DAMP; n.vy *= DAMP;
      n.x += Math.max(-30, Math.min(30, n.vx));
      n.y += Math.max(-30, Math.min(30, n.vy));
    });
  }

  // ---- interaction ----
  var hover = null, selected = null, dragging = null;
  var pointer = { down: false, moved: 0, x: 0, y: 0, panning: false };

  function nodeAt(px, py) {
    var w = toWorld(px, py), best = null, bd = Infinity;
    nodes.forEach(function (n) {
      var dx = n.x - w.x, dy = n.y - w.y;
      var d = Math.sqrt(dx * dx + dy * dy);
      if (d < n.r / 1 + 8 / cam.scale && d < bd) { bd = d; best = n; }
    });
    return best;
  }
  function rel(ev) {
    var rc = canvas.getBoundingClientRect();
    var t = ev.touches ? ev.touches[0] : ev;
    return { x: t.clientX - rc.left, y: t.clientY - rc.top };
  }
  canvas.addEventListener("pointerdown", function (ev) {
    var p = rel(ev);
    pointer.down = true; pointer.moved = 0; pointer.x = p.x; pointer.y = p.y;
    var hit = nodeAt(p.x, p.y);
    if (hit) { dragging = hit; hit.vx = hit.vy = 0; }
    else { pointer.panning = true; }
    canvas.setPointerCapture(ev.pointerId);
  });
  canvas.addEventListener("pointermove", function (ev) {
    var p = rel(ev);
    if (pointer.down) {
      var dx = p.x - pointer.x, dy = p.y - pointer.y;
      pointer.moved += Math.abs(dx) + Math.abs(dy);
      if (dragging) {
        var w = toWorld(p.x, p.y);
        dragging.x = w.x; dragging.y = w.y; dragging.vx = dragging.vy = 0;
        settleFrames = 120;
      } else if (pointer.panning) {
        cam.x += dx; cam.y += dy;
      }
      pointer.x = p.x; pointer.y = p.y;
    } else {
      var h = nodeAt(p.x, p.y);
      if (h !== hover) { hover = h; canvas.style.cursor = h ? "pointer" : "grab"; }
    }
  });
  function endPointer() {
    if (pointer.down && pointer.moved < 5 && dragging) select(dragging);
    else if (pointer.down && pointer.moved < 5 && pointer.panning) select(null);
    pointer.down = false; pointer.panning = false; dragging = null;
  }
  canvas.addEventListener("pointerup", endPointer);
  canvas.addEventListener("pointercancel", endPointer);
  canvas.addEventListener("wheel", function (ev) {
    ev.preventDefault();
    var p = rel(ev);
    var before = toWorld(p.x, p.y);
    var k = Math.exp(-ev.deltaY * 0.0012);
    cam.scale = Math.max(0.25, Math.min(3, cam.scale * k));
    cam.x = p.x - before.x * cam.scale;
    cam.y = p.y - before.y * cam.scale;
  }, { passive: false });

  // ---- detail panel ----
  var panel = document.getElementById("panel");
  var panelBody = document.getElementById("panel-body");
  var panelClose = document.getElementById("panel-close");
  if (panelClose) panelClose.addEventListener("click", function () { select(null); });

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function select(n) {
    selected = n;
    if (!n) { panel.hidden = true; return; }
    var d = n.detail;
    var html = "";
    if (!d && n.type === "tech") {
      var used = (techUse[n.id] || []).filter(function (v, i, a) { return a.indexOf(v) === i; });
      d = { kind: "tech", title: n.label, body: used.length ? "Used in: " + used.join(", ") : "Part of the stack." };
    }
    html += '<p class="ptype">' + esc(d.kind) + "</p>";
    html += "<h3>" + esc(d.title) + (d.team ? ' <span class="pill">team</span>' : "") + "</h3>";
    if (d.body) html += "<p>" + esc(d.body) + "</p>";
    if (d.meta) html += '<p style="font-size:.78rem">' + esc(d.meta) + "</p>";
    if (d.highlights) {
      html += "<ul>";
      d.highlights.forEach(function (h) { html += "<li>" + esc(h) + "</li>"; });
      html += "</ul>";
    }
    if (d.stack) {
      html += '<div class="chips">';
      d.stack.forEach(function (s) { html += '<span class="chip">' + esc(s) + "</span>"; });
      html += "</div>";
    }
    if (d.repo) html += '<a class="plink" href="' + esc(d.repo) + '" target="_blank" rel="noopener">source →</a>';
    if (d.links) {
      Object.keys(d.links).forEach(function (k) {
        html += '<a class="plink" href="' + esc(d.links[k]) + '" target="_blank" rel="noopener">' + esc(k) + " →</a>";
      });
    }
    panelBody.innerHTML = html;
    panel.hidden = false;
  }

  // ---- render ----
  function draw() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    ctx.save();
    ctx.translate(cam.x, cam.y);
    ctx.scale(cam.scale, cam.scale);

    var focus = hover || selected;
    var lit = null;
    if (focus) { lit = new Set(neighbours[focus.id]); lit.add(focus.id); }

    ctx.lineWidth = 1 / cam.scale;
    edges.forEach(function (e) {
      var on = lit && lit.has(e.s.id) && lit.has(e.t.id);
      ctx.strokeStyle = on ? colorFor("project") : css("--border");
      ctx.globalAlpha = lit ? (on ? 0.9 : 0.15) : 0.5;
      ctx.beginPath();
      ctx.moveTo(e.s.x, e.s.y);
      ctx.lineTo(e.t.x, e.t.y);
      ctx.stroke();
    });
    ctx.globalAlpha = 1;

    nodes.forEach(function (n) {
      var dim = lit && !lit.has(n.id);
      ctx.globalAlpha = dim ? 0.25 : 1;
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
      ctx.fillStyle = colorFor(n.type);
      ctx.fill();
      if (n === selected) {
        ctx.lineWidth = 2 / cam.scale;
        ctx.strokeStyle = css("--text");
        ctx.stroke();
      }
      var showLabel;
      if (n.type === "tech") showLabel = n === hover || (lit && lit.has(n.id)) || cam.scale > 1.4;
      else showLabel = !dim || n === hover;
      if (showLabel) {
        ctx.globalAlpha = dim ? 0.3 : 1;
        ctx.fillStyle = css("--text");
        ctx.font = (n.type === "person" ? "600 " : "") + Math.max(11, 12 / cam.scale) + "px ui-monospace, Menlo, monospace";
        ctx.textAlign = "center";
        ctx.fillText(n.label, n.x, n.y + n.r + 13 / cam.scale);
      }
    });
    ctx.restore();
    ctx.globalAlpha = 1;
  }

  var autoFit = reduced ? 0 : 140;
  function frame() {
    if (!document.documentElement.classList.contains("list")) {
      var iters = autoFit > 90 ? 4 : settleFrames > 0 ? 2 : 1;
      for (var i = 0; i < iters; i++) step();
      if (autoFit > 0) { autoFit--; fit(autoFit > 60 ? 0.16 : 0.06); }
      if (settleFrames > 0) settleFrames--;
      draw();
    }
    requestAnimationFrame(frame);
  }

  window.addEventListener("resize", function () { resize(); autoFit = Math.max(autoFit, 30); });
  window.addEventListener("themechange", draw);
  window.addEventListener("viewchange", function () { resize(); autoFit = Math.max(autoFit, 60); });
  resize();
  fit();
  cam.scale *= 0.35; // start zoomed-out; nodes burst outward, then autoFit eases in
  requestAnimationFrame(frame);
})();
