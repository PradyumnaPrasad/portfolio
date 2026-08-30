// Drives the three Workshop tools with plain fetch.
(function () {
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function renderSearch(out, data, modeEl) {
    if (modeEl && data.results.length) modeEl.textContent = "· " + data.results[0].mode;
    if (!data.results.length) {
      out.innerHTML = '<p class="muted">No matches.</p>';
      return;
    }
    out.innerHTML = data.results
      .map(function (r) {
        return (
          '<div class="hit"><span class="tag">' + esc(r.kind) + "</span> " +
          "<b>" + esc(r.title) + "</b> <span class=\"muted\">" + r.score + "</span>" +
          "<p>" + esc(r.text) + "</p>" +
          (r.ref && r.ref !== "/" ? '<a class="qlink" href="' + esc(r.ref) + '" target="_blank" rel="noopener">source →</a>' : "") +
          "</div>"
        );
      })
      .join("");
  }

  function renderAsk(out, data) {
    var h = "";
    if (data.answer) h += '<p class="answer">' + esc(data.answer) + "</p>";
    else if (data.disabled) h += '<p class="muted">Chatbot disabled (no API key). Passages that would be used:</p>';
    else if (data.error) h += '<p class="warn">' + esc(data.error) + "</p>";
    if (data.sources && data.sources.length) {
      h += '<div class="chips">' + data.sources
        .map(function (s) {
          var label = esc(s.title);
          return s.ref && s.ref !== "/"
            ? '<a class="chip" href="' + esc(s.ref) + '" target="_blank" rel="noopener">' + label + "</a>"
            : '<span class="chip">' + label + "</span>";
        })
        .join("") + "</div>";
    }
    out.innerHTML = h || '<p class="muted">No answer.</p>';
  }

  function renderClf(out, data) {
    if (!data.predictions.length) {
      out.innerHTML = '<p class="muted">Enter some text.</p>';
      return;
    }
    out.innerHTML =
      '<div class="bars">' +
      data.predictions
        .map(function (p) {
          var pct = Math.round(p.prob * 100);
          return (
            '<div class="langrow"><span class="lname">' + esc(p.label) + "</span>" +
            '<span class="track"><i style="width:' + pct + '%;background:var(--gold);"></i></span>' +
            '<span class="lpct">' + pct + "%</span></div>"
          );
        })
        .join("") +
      "</div>";
  }

  document.querySelectorAll(".wform").forEach(function (form) {
    var tool = form.closest(".wtool");
    var out = tool.querySelector("[data-out]");
    var modeEl = tool.querySelector("[data-mode]");
    var endpoint = form.dataset.endpoint;
    var method = form.dataset.method || "get";
    var field = form.querySelector("input").name;

    function run(value) {
      value = (value || "").trim();
      if (!value) return;
      out.innerHTML = '<p class="muted">…</p>';
      var opts, url;
      if (method === "post") {
        url = endpoint;
        var payload = {};
        payload[field] = value;
        opts = { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) };
      } else {
        url = endpoint + "?" + new URLSearchParams([[field, value]]).toString();
        opts = {};
      }
      fetch(url, opts)
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (res) {
          if (!res.ok && res.d.error) { out.innerHTML = '<p class="warn">' + esc(res.d.error) + "</p>"; return; }
          if (endpoint.indexOf("search") > -1) renderSearch(out, res.d, modeEl);
          else if (endpoint.indexOf("ask") > -1) renderAsk(out, res.d);
          else renderClf(out, res.d);
        })
        .catch(function () { out.innerHTML = '<p class="warn">Request failed.</p>'; });
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      run(form.querySelector("input").value);
    });
    tool.querySelectorAll(".suggest button").forEach(function (b) {
      b.addEventListener("click", function () {
        form.querySelector("input").value = b.textContent;
        run(b.textContent);
      });
    });
  });
})();
