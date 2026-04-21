/**
 * analyzer.js — Index page controller
 * Collects form data, calls /api/analyze, redirects to dashboard
 */

document.addEventListener("DOMContentLoaded", () => {
  const btn      = document.getElementById("analyzeBtn");
  const btnText  = document.getElementById("btnText");
  const spinner  = document.getElementById("btnSpinner");
  const errorMsg = document.getElementById("errorMsg");

  btn.addEventListener("click", async () => {
    clearError();

    // ── Collect inputs ──────────────────────────────────────────
    const followers = parseFloat(document.getElementById("followers").value) || 0;
    const following = parseFloat(document.getElementById("following").value) || 0;
    const age       = parseFloat(document.getElementById("age").value) || 0;

    if (followers <= 0 && following <= 0 && age <= 0) {
      showError("Please fill in at least Followers, Following, and Account Age.");
      return;
    }

    const payload = {
      username:            document.getElementById("username").value.trim(),
      bio:                 document.getElementById("bio").value.trim(),
      caption:             document.getElementById("caption").value.trim(),
      followers_count:     followers,
      following_count:     following,
      account_age_days:    age,
      total_posts:         parseFloat(document.getElementById("posts").value) || 0,
      avg_likes:           parseFloat(document.getElementById("likes").value) || 0,
      avg_comments:        parseFloat(document.getElementById("comments").value) || 0,
      has_profile_picture: document.getElementById("has_pic").checked,
    };

    // ── Loading state ───────────────────────────────────────────
    setLoading(true);

    try {
      const res  = await fetch("/api/analyze", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Server error" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const json = await res.json();
      if (!json.success) throw new Error("Analysis failed");

      // Store result and redirect
      sessionStorage.setItem("analysisResult", JSON.stringify({
        ...json.data,
        _username: payload.username || "unknown",
      }));
      window.location.href = "/dashboard";

    } catch (err) {
      showError(`Analysis error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  });

  function setLoading(on) {
    btn.disabled = on;
    btnText.classList.toggle("hidden", on);
    spinner.classList.toggle("hidden", !on);
  }

  function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.classList.remove("hidden");
  }

  function clearError() {
    errorMsg.classList.add("hidden");
    errorMsg.textContent = "";
  }
});
