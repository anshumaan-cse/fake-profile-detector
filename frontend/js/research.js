/**
 * research.js — Research / Evaluation page controller
 * Fetches /api/evaluation/summary and renders metrics, charts, confusion matrices
 */

document.addEventListener("DOMContentLoaded", async () => {
  // Chart.js defaults
  Chart.defaults.color        = "rgba(240,244,255,0.5)";
  Chart.defaults.borderColor  = "rgba(255,255,255,0.06)";
  Chart.defaults.font.family  = "Inter, sans-serif";

  try {
    const res = await fetch("/api/evaluation/summary");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    renderModelCards(data.models);
    renderROCChart(data.models);
    renderImportanceChart(data.feature_importances);
    renderConfusionMatrix("cmLR", data.models[0].confusion_matrix, "LR");
    renderConfusionMatrix("cmRF", data.models[1].confusion_matrix, "RF");
    renderMetricsBarChart(data.models);

  } catch (err) {
    document.getElementById("modelMetricsGrid").innerHTML =
      `<div class="loading-state" style="color:#ff4d6d;">
        ⚠ Could not load evaluation data: ${err.message}
      </div>`;
  }
});


// ── Model Metric Cards ────────────────────────────────────────────
function renderModelCards(models) {
  const grid = document.getElementById("modelMetricsGrid");
  grid.innerHTML = models.map(m => `
    <div class="model-metric-card glass-card">
      <div class="model-name">${modelIcon(m.name)} ${m.name}</div>
      <div class="metrics-row">
        <div class="metric-box metric-accuracy">
          <div class="metric-box-val">${pct(m.accuracy)}</div>
          <div class="metric-box-lbl">ACCURACY</div>
        </div>
        <div class="metric-box metric-precision">
          <div class="metric-box-val">${pct(m.precision)}</div>
          <div class="metric-box-lbl">PRECISION</div>
        </div>
        <div class="metric-box metric-recall">
          <div class="metric-box-val">${pct(m.recall)}</div>
          <div class="metric-box-lbl">RECALL</div>
        </div>
        <div class="metric-box metric-f1">
          <div class="metric-box-val">${pct(m.f1_score)}</div>
          <div class="metric-box-lbl">F1 SCORE</div>
        </div>
      </div>
      <div style="margin-top:12px;display:flex;align-items:center;gap:10px;">
        <span style="font-size:11px;color:var(--text-muted);">ROC AUC</span>
        <div style="flex:1;height:6px;background:rgba(255,255,255,0.07);border-radius:3px;overflow:hidden;">
          <div style="height:100%;width:${m.roc_auc*100}%;background:linear-gradient(90deg,#a78bfa,#00d4ff);border-radius:3px;transition:width 1s;"></div>
        </div>
        <span style="font-size:13px;font-weight:700;color:#a78bfa;">${m.roc_auc.toFixed(3)}</span>
      </div>
    </div>
  `).join("");
}


// ── ROC Curve Chart ───────────────────────────────────────────────
function renderROCChart(models) {
  const colors = ["#4f9eff", "#00ffa6"];
  const datasets = models.map((m, i) => ({
    label:       `${m.name} (AUC=${m.roc_auc.toFixed(3)})`,
    data:        m.roc_curve.fpr.map((x, j) => ({ x, y: m.roc_curve.tpr[j] })),
    borderColor: colors[i],
    backgroundColor: "transparent",
    borderWidth: 2,
    pointRadius: 0,
    tension:     0.3,
  }));

  // Add random classifier diagonal
  datasets.push({
    label: "Random Classifier",
    data:  [{ x:0, y:0 }, { x:1, y:1 }],
    borderColor: "rgba(255,255,255,0.2)",
    borderDash: [6, 4],
    borderWidth: 1,
    pointRadius: 0,
    backgroundColor: "transparent",
  });

  new Chart(document.getElementById("rocChart"), {
    type: "scatter",
    data: { datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      showLine: true,
      plugins: { legend: { position:"bottom" } },
      scales: {
        x: { min:0, max:1, title:{ display:true, text:"False Positive Rate" },
             grid:{ color:"rgba(255,255,255,0.05)" } },
        y: { min:0, max:1, title:{ display:true, text:"True Positive Rate" },
             grid:{ color:"rgba(255,255,255,0.05)" } },
      }
    }
  });
}


// ── Feature Importance Chart ──────────────────────────────────────
function renderImportanceChart(importances) {
  const entries = Object.entries(importances)
    .sort((a, b) => b[1] - a[1]);

  const labels = entries.map(([k]) => k.replace(/_/g, " "));
  const values = entries.map(([, v]) => +(v * 100).toFixed(2));

  new Chart(document.getElementById("importanceChart"), {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Importance (%)",
        data: values,
        backgroundColor: values.map((v, i) => {
          const t = i / values.length;
          return `hsl(${180 + t * 120}, 70%, 55%)`;
        }),
        borderRadius: 5,
        borderSkipped: false,
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true, maintainAspectRatio: false,
      plugins: { legend:{ display:false } },
      scales: {
        x: { beginAtZero:true, grid:{ color:"rgba(255,255,255,0.05)" },
             ticks:{ callback: v => `${v}%` } },
        y: { grid:{ display:false }, ticks:{ font:{ size:11 } } }
      }
    }
  });
}


// ── Confusion Matrix ──────────────────────────────────────────────
function renderConfusionMatrix(containerId, cm, prefix) {
  // cm = [[TN, FP], [FN, TP]]
  const tn = cm[0][0], fp = cm[0][1];
  const fn = cm[1][0], tp = cm[1][1];

  document.getElementById(containerId).innerHTML = `
    <div class="cm-wrap">
      <div class="cm-cell cm-tn">
        <div class="cm-cell-label">TN (Real→Real)</div>
        <div class="cm-cell-value">${tn}</div>
      </div>
      <div class="cm-cell cm-fp">
        <div class="cm-cell-label">FP (Real→Fake)</div>
        <div class="cm-cell-value">${fp}</div>
      </div>
      <div class="cm-cell cm-fn">
        <div class="cm-cell-label">FN (Fake→Real)</div>
        <div class="cm-cell-value">${fn}</div>
      </div>
      <div class="cm-cell cm-tp">
        <div class="cm-cell-label">TP (Fake→Fake)</div>
        <div class="cm-cell-value">${tp}</div>
      </div>
    </div>
  `;
}


// ── Grouped Metrics Bar Chart ─────────────────────────────────────
function renderMetricsBarChart(models) {
  const metricKeys = ["accuracy", "precision", "recall", "f1_score", "roc_auc"];
  const labels     = ["Accuracy", "Precision", "Recall", "F1 Score", "ROC AUC"];
  const colors     = ["#4f9eff", "#00ffa6"];

  const datasets = models.map((m, i) => ({
    label:           m.name,
    data:            metricKeys.map(k => +(m[k] * 100).toFixed(2)),
    backgroundColor: colors[i] + "bb",
    borderColor:     colors[i],
    borderWidth:     1,
    borderRadius:    5,
  }));

  new Chart(document.getElementById("metricsBarChart"), {
    type: "bar",
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position:"bottom" } },
      scales: {
        y: { beginAtZero:true, max:100,
             grid:{ color:"rgba(255,255,255,0.05)" },
             ticks:{ callback: v => `${v}%` } },
        x: { grid:{ display:false } }
      }
    }
  });
}


// ── Helpers ───────────────────────────────────────────────────────
function pct(v) { return `${(v * 100).toFixed(1)}%`; }
function modelIcon(name) {
  return name.includes("Logistic") ? "📈" : "🌲";
}
