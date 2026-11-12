(function () {
  "use strict";
  var D = /*DATA*/null;
  var CH = { cat: ["#24599e", "#d9711c", "#12929f", "#c8423b", "#6b45b8", "#7c9a12", "#b03a72", "#a87b00"],
    navy: "#16213a", ink: "#262b33", ink2: "#5d6470", meta: "#6b7280", frame: "#cfcfcf", grid: "#e5e5e5",
    ramp: ["#16213a", "#3d5f99", "#7f98c2"] };
  var CONFIG = { displayModeBar: false, scrollZoom: false, responsive: true };
  var drawn = {}, wasNarrow = null, current = "summary";

  function narrow() { return window.innerWidth < 700; }
  function axis(opts) {
    var a = { showgrid: false, linecolor: CH.frame, tickcolor: CH.frame, tickfont: { color: CH.meta, size: 11 }, fixedrange: true, zeroline: false, automargin: true, tickangle: 0 };
    Object.keys(opts || {}).forEach(function (k) { a[k] = opts[k]; });
    if (opts && opts.value) { a.showgrid = true; a.gridcolor = CH.grid; delete a.value; }
    if (a.title && typeof a.title === "string") { a.title = { text: a.title, font: { size: 12, color: CH.ink2 } }; }
    return a;
  }
  function base(extra) {
    var l = { paper_bgcolor: "#ffffff", plot_bgcolor: "#ffffff", font: { family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif", color: CH.ink, size: 12 },
      margin: { l: 64, r: 16, t: 8, b: 64 }, hovermode: "closest", hoverlabel: { bgcolor: "#ffffff", bordercolor: CH.frame, font: { color: CH.ink } },
      legend: { orientation: "h", x: 0.5, xanchor: "center", y: -0.2, yanchor: "top", font: { size: 12 } }, showlegend: true };
    Object.keys(extra || {}).forEach(function (k) { l[k] = extra[k]; });
    return l;
  }
  function fmt(x, d, sign) {
    var s = Math.abs(x).toFixed(d);
    if (x < 0 && Number(s) !== 0) { return "−" + s; }
    if (sign && Number(s) !== 0) { return "+" + s; }
    return s;
  }
  function zero() { return { type: "line", xref: "x", yref: "paper", x0: 0, x1: 0, y0: 0, y1: 1, line: { color: CH.frame, width: 1.5 } }; }
  function intervals(rows, offset, name, colour, unit) {
    return { x: rows.map(function (r) { return r[0]; }), y: rows.map(function (r, i) { return i + offset; }), mode: "markers", type: "scatter", name: name,
      marker: { color: colour, size: 9 },
      error_x: { type: "data", symmetric: false, array: rows.map(function (r) { return r[2] - r[0]; }), arrayminus: rows.map(function (r) { return r[0] - r[1]; }), color: colour, thickness: 2, width: 0 },
      text: rows.map(function (r, i) { return D.factors[i] + ": " + fmt(r[0], 3, true) + unit + ", interval " + fmt(r[1], 3) + " to " + fmt(r[2], 3); }), hoverinfo: "text" };
  }
  function factorAxis() {
    return axis({ tickvals: [0, 1, 2, 3, 4, 5], ticktext: D.factors, autorange: false, range: [5.6, -0.6], tickfont: { size: 12, color: CH.ink } });
  }

  // the months after the sample: two comparisons, each difference with its interval
  function fAfter() {
    var traces = [intervals(D.after.rt, -0.16, "Real-time combination minus real-time original", CH.cat[0], ", annualised"),
      intervals(D.after.vm, 0.16, "Volatility-managed minus original", CH.cat[1], ", annualised")];
    var layout = base({ shapes: [zero()] });
    layout.xaxis = axis({ value: true, range: [-1.25, 1.05], title: "Sharpe ratio difference, annualised", dtick: narrow() ? 0.5 : 0.25 });
    layout.yaxis = factorAxis();
    layout.legend.y = narrow() ? -0.3 : -0.2;
    Plotly.newPlot("c-after", traces, layout, CONFIG);
  }
  // Moreira and Muir's sample, on the same axis
  function fMM() {
    var traces = [intervals(D.mm, 0, "Volatility-managed minus original", CH.cat[1], ", annualised")];
    var layout = base({ shapes: [zero()], showlegend: false, margin: { l: 64, r: 16, t: 8, b: 48 } });
    layout.xaxis = axis({ value: true, range: [-1.25, 1.05], title: "Sharpe ratio difference, annualised", dtick: narrow() ? 0.5 : 0.25 });
    layout.yaxis = factorAxis();
    Plotly.newPlot("c-mm", traces, layout, CONFIG);
  }
  // the alpha gross and net of costs, plus or minus two standard errors
  function fCosts() {
    function tr(rows, offset, name, colour) {
      return { x: rows.map(function (r) { return r[0]; }), y: rows.map(function (r, i) { return i + offset; }), mode: "markers", type: "scatter", name: name,
        marker: { color: colour, size: 8 },
        error_x: { type: "data", symmetric: true, array: rows.map(function (r) { return 2 * r[1]; }), color: colour, thickness: 2, width: 0 },
        text: rows.map(function (r, i) { return D.factors[i] + ", " + name + ": " + fmt(r[0], 2) + "% a year, standard error " + fmt(r[1], 2); }), hoverinfo: "text" };
    }
    var traces = [tr(D.costs.gross, -0.22, "gross", CH.ramp[0]), tr(D.costs.net10, 0, "net of 10 bp", CH.ramp[1]), tr(D.costs.net20, 0.22, "net of 20 bp", CH.ramp[2])];
    var layout = base({ shapes: [zero()] });
    layout.xaxis = axis({ value: true, range: [-6, 18], title: "alpha, % a year", dtick: narrow() ? 4 : 2 });
    layout.yaxis = factorAxis();
    layout.legend.y = narrow() ? -0.3 : -0.22;
    Plotly.newPlot("c-costs", traces, layout, CONFIG);
  }
  // the market's position month by month
  function fPos() {
    var x = D.position.months.map(function (m) { return m + "-15"; });
    var traces = [{ x: x, y: D.position.values, mode: "lines", type: "scatter", line: { color: CH.navy, width: 1 }, name: "position", hovertemplate: "%{x|%b %Y}: %{y:.2f}<extra></extra>" }];
    function level(y, label) {
      return { shape: { type: "line", xref: "paper", yref: "y", x0: 0, x1: 1, y0: y, y1: y, line: { color: CH.ink2, width: 1.5, dash: "dash" } },
        note: { xref: "paper", yref: "y", x: 1, y: Math.log10(y), xanchor: "right", yanchor: "bottom", text: label, showarrow: false, font: { size: 12, color: CH.ink2 }, bgcolor: "rgba(255,255,255,0.85)" } };
    }
    var a = level(D.position.p50, "median " + fmt(D.position.p50, 2)), b = level(D.position.p99, "99th percentile " + fmt(D.position.p99, 2));
    var layout = base({ showlegend: false, shapes: [a.shape, b.shape], annotations: [a.note, b.note], margin: { l: 56, r: 16, t: 8, b: 40 } });
    layout.xaxis = axis({ type: "date", tickformat: "%Y", dtick: narrow() ? "M240" : "M120" });
    layout.yaxis = axis({ value: true, type: "log", range: [-2, 1.35], title: "position", tickvals: [0.01, 0.1, 1, 10], ticktext: ["0.01", "0.1", "1", "10"] });
    Plotly.newPlot("c-position", traces, layout, CONFIG);
  }

  var VIEWS = { summary: [fAfter], after: [], "in-sample": [fMM, fCosts, fPos], replication: [], method: [] };
  function drawView(name) { if (drawn[name]) { return; } VIEWS[name].forEach(function (fn) { fn(); }); drawn[name] = true; }
  function showView(name, scrollTo) {
    current = name;
    document.querySelectorAll(".view").forEach(function (s) { s.classList.toggle("on", s.id === name); });
    document.querySelectorAll("[data-view]").forEach(function (b) { b.setAttribute("aria-selected", String(b.getAttribute("data-view") === name)); });
    if (typeof Plotly !== "undefined") { drawView(name); }
    if (scrollTo) { var el = document.getElementById(scrollTo); if (el) { el.scrollIntoView({ block: "start" }); } }
  }
  function viewOf(id) { var el = document.getElementById(id); while (el && !(el.classList && el.classList.contains("view"))) { el = el.parentElement; } if (el) { return el.id; } return null; }
  function route() {
    var h = (location.hash || "").replace("#", "");
    if (VIEWS[h]) { showView(h); return; }
    if (h && document.getElementById(h)) { var v = viewOf(h); if (v) { showView(v, h); return; } showView("method", h); return; }
    showView("summary");
  }
  document.querySelectorAll("[data-view]").forEach(function (b) { b.addEventListener("click", function () { var v = b.getAttribute("data-view"); history.replaceState(null, "", "#" + v); showView(v); window.scrollTo(0, 0); }); });
  window.addEventListener("hashchange", route);
  document.addEventListener("click", function (e) {
    var a = e.target.closest ? e.target.closest('a[href^="#"]') : null;
    if (!a) { return; }
    var id = a.getAttribute("href").slice(1), v = viewOf(id);
    if (v && v !== current) { e.preventDefault(); history.replaceState(null, "", "#" + id); showView(v, id); }
  });
  var timer = null;
  window.addEventListener("resize", function () {
    clearTimeout(timer);
    timer = setTimeout(function () { var n = narrow(); if (n !== wasNarrow) { wasNarrow = n; drawn = {}; if (typeof Plotly !== "undefined") { drawView(current); } } }, 200);
  });
  if (typeof Plotly === "undefined") {
    document.querySelectorAll(".chart").forEach(function (el) { el.textContent = "The charting library did not load. This page needs a connection to cdn.plot.ly once, and every figure's numbers are in the table under it."; });
  }
  wasNarrow = narrow();
  route();
  // the fade at the tab bar's right edge shows only while more of the bar lies to the right
  (function () {
    var bar = document.querySelector(".tabs"), row = bar.querySelector(".wrap");
    function upd() { bar.classList.toggle("more", row.scrollWidth - row.clientWidth - row.scrollLeft > 1); }
    if (!("ResizeObserver" in window)) { return; }
    row.addEventListener("scroll", upd);
    new ResizeObserver(upd).observe(row);
    upd();
  })();
  // the fade at a table's right edge shows only while more of the table lies to the right
  document.querySelectorAll(".tw").forEach(function (t) {
    function upd() { var s = t.firstElementChild; t.classList.toggle("more", !!s && s.scrollWidth - s.clientWidth - s.scrollLeft > 1); }
    if (!("ResizeObserver" in window)) { t.classList.add("more"); return; }
    t.addEventListener("scroll", upd, true);
    new ResizeObserver(upd).observe(t);
    upd();
  });
})();
