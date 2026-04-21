/**
 * dashboard.js — Analysis Dashboard controller
 * Reads sessionStorage result and renders all UI components + charts
 */

document.addEventListener("DOMContentLoaded", () => {
  const raw = sessionStorage.getItem("analysisResult");

  if (!raw) {
    // No data – redirect back
    window.location.href = "/";
    return;
  }

  const d = JSON.parse(raw);
  render(d);
});

// ── Chart.js global defaults ──────────────────────────────────────
Chart.defaults.color            = "rgba(240,244,255,0.5)";
Chart.defaults.borderColor      = "rgba(255,255,255,0.06)";
Chart.defaults.font.family      = "Inter, sans-serif";
Chart.defaults.plugins.legend.labels.boxWidth = 12;


function render(d) {
  const username = d._username || "unknown";

  // ── Status badge ──────────────────────────────────────────────
  const badge = document.getElementById("statusBadge");
  badge.textContent = d.status;
  badge.className   = "status-badge " + statusClass(d.status);

  // ── Profile name ──────────────────────────────────────────────
  document.getElementById("profileUsername").textContent =
    username ? `@${username}` : "Profile Analysis";

  // ── Explanation ───────────────────────────────────────────────
  document.getElementById("explanationText").textContent = d.explanation;

  // ── Score display ─────────────────────────────────────────────
  const hybrid = d.hybrid_score;
  document.getElementById("riskScoreDisplay").textContent = `${Math.round(hybrid)}%`;
  document.getElementById("riskScoreDisplay").style.color = scoreColor(hybrid);

  // ── Score bars ────────────────────────────────────────────────
  animateBar("ruleBar",   "ruleScore",   d.rule_score,        "/100");
  animateBar("rfBar",     "rfScore",     d.ml_rf_probability, "%");
  animateBar("lrBar",     "lrScore",     d.ml_lr_probability, "%");
  animateBar("hybridBar", "hybridScore", hybrid,              "%");

  // ── Risk gauge ────────────────────────────────────────────────
  drawGauge(hybrid);

  // ── Metric cards ─────────────────────────────────────────────
  const f = d.features;
  setMetric("mc-followers",  fmt(f.followers_count));
  setMetric("mc-following",  fmt(f.following_count));
  setMetric("mc-engagement", `${f.engagement_rate.toFixed(1)}%`);
  setMetric("mc-age",        `${f.account_age_days}d`);
  setMetric("mc-posts",      f.posts_per_week.toFixed(1));
  setMetric("mc-riskScore",  `${Math.round(hybrid)}%`);

  // ── Feature contribution chart ────────────────────────────────
  renderFeatureChart(d.flag_weights);

  // ── Model comparison chart ────────────────────────────────────
  renderComparisonChart(d.model_comparison);

  // ── Flags list ────────────────────────────────────────────────
  renderFlags(d.flags, d.flag_weights);

  // ── Anomalies ─────────────────────────────────────────────────
  renderAnomalies(d.anomalies);

  // ── Feature table ─────────────────────────────────────────────
  renderFeatureTable(f);
}


// ── Gauge chart ───────────────────────────────────────────────────
function drawGauge(score) {
  const color = scoreColor(score);
  const safe  = Math.max(0, 100 - score);

  new Chart(document.getElementById("riskGauge"), {
    type: "doughnut",
    data: {
      datasets: [{
        data: [score, safe],
        backgroundColor: [color, "rgba(255,255,255,0.05)"],
        borderWidth: 0,
      }]
    },
    options: {
      cutout:      "78%",
      rotation:    -90,
      circumference: 180,
      plugins:     { legend: { display: false }, tooltip: { enabled: false } },
      animation:   { duration: 1200, easing: "easeOutQuart" },
    }
  });
}


// ── Feature contribution bar chart ────────────────────────────────
function renderFeatureChart(flagWeights) {
  const entries = Object.entries(flagWeights)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);

  if (entries.length === 0) {
    document.getElementById("featureChart").closest(".chart-card")
      .querySelector(".chart-wrap").innerHTML =
      `<p style="color:var(--green);text-align:center;padding:40px;font-size:13px;">
        ✅ No significant risk flags triggered
      </p>`;
    return;
  }

  const labels = entries.map(([k]) => truncate(k, 40));
  const values = entries.map(([, v]) => v);
  const colors = values.map(v =>
    v > 15 ? "#ff4d6d" : v > 8 ? "#ffb347" : "#4f9eff"
  );

  new Chart(document.getElementById("featureChart"), {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Weighted Penalty",
        data:  values,
        backgroundColor: colors,
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { beginAtZero: true, grid: { color: "rgba(255,255,255,0.05)" } },
        y: { grid: { display: false }, ticks: { font: { size: 11 } } }
      }
    }
  });
}


// ── Model comparison radar/bar ─────────────────────────────────────
function renderComparisonChart(mc) {
  new Chart(document.getElementById("comparisonChart"), {
    type: "bar",
    data: {
      labels: ["Rule-Based", "ML (RF)", "ML (LR)", "Hybrid"],
      datasets: [{
        label: "Risk Score (%)",
        data: [mc.rule_based, mc.ml_rf, mc.ml_lr, mc.hybrid],
        backgroundColor: [
          "rgba(79,158,255,0.7)",
          "rgba(0,255,166,0.7)",
          "rgba(255,179,71,0.7)",
          "rgba(0,212,255,0.9)",
        ],
        borderRadius: 8,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: ctx => ` ${ctx.raw.toFixed(1)}%` }
        }
      },
      scales: {
        y: { beginAtZero: true, max: 100, grid: { color:"rgba(255,255,255,0.05)" } },
        x: { grid: { display: false } }
      },
      animation: { duration: 1000, easing: "easeOutBounce" }
    }
  });
}


// ── Flags list ────────────────────────────────────────────────────
function renderFlags(flags, weights) {
  const el = document.getElementById("flagsList");
  if (!flags || flags.length === 0) {
    el.innerHTML = `<div class="no-flags">✅ No rule violations detected</div>`;
    return;
  }

  el.innerHTML = flags.map(f => {
    const w = (weights[f] || 0).toFixed(1);
    return `<div class="flag-item">
      <span class="flag-weight">+${w}</span>
      <span>${f}</span>
    </div>`;
  }).join("");
}


// ── Anomalies ─────────────────────────────────────────────────────
function renderAnomalies(anomalies) {
  const el = document.getElementById("anomalyList");
  if (!anomalies || anomalies.length === 0) {
    el.innerHTML = `<div class="no-flags">✅ No behavioral anomalies detected</div>`;
    return;
  }
  el.innerHTML = anomalies.map(a =>
    `<div class="anomaly-item">⚠ ${a}</div>`
  ).join("");
}


// ── Feature table ─────────────────────────────────────────────────
function renderFeatureTable(features) {
  const labels = {
    followers_count:     "Followers",
    following_count:     "Following",
    engagement_rate:     "Engagement Rate",
    account_age_days:    "Account Age (days)",
    posts_per_week:      "Posts / Week",
    bio_length:          "Bio Length (chars)",
    profile_picture:     "Has Profile Pic",
    username_randomness: "Username Randomness",
    spam_keyword_score:  "Spam Keyword Score",
    ff_ratio:            "F/F Ratio",
  };

  const el = document.getElementById("featureTable");
  el.innerHTML = Object.entries(labels)
    .map(([key, label]) => {
      let val = features[key];
      if (key === "profile_picture") val = val ? "Yes ✓" : "No ✗";
      else if (typeof val === "number") val = val.toFixed ? val.toFixed(3) : val;
      return `<div class="ft-row">
        <span class="ft-key">${label}</span>
        <span class="ft-value">${val ?? "—"}</span>
      </div>`;
    }).join("");
}


// ── Helpers ───────────────────────────────────────────────────────
function animateBar(barId, valId, value, suffix) {
  document.getElementById(valId).textContent = `${Math.round(value)}${suffix}`;
  setTimeout(() => {
    document.getElementById(barId).style.width = `${Math.min(value, 100)}%`;
  }, 100);
}

function setMetric(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function statusClass(status) {
  if (status === "REAL")      return "status-real";
  if (status === "SUSPICIOUS") return "status-suspicious";
  return "status-high-risk";
}

function scoreColor(score) {
  if (score < 35) return "#00ffa6";
  if (score < 65) return "#ffb347";
  return "#ff4d6d";
}

function fmt(n) {
  if (n >= 1_000_000) return `${(n/1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${(n/1_000).toFixed(1)}K`;
  return `${n}`;
}

function truncate(str, max) {
  return str.length > max ? str.slice(0, max - 1) + "…" : str;
}
