 document.addEventListener("DOMContentLoaded", () => {

    const raw = localStorage.getItem("analysisData");

    if (!raw) {
        alert("No data found. Go back and analyze first.");
        window.location.href = "index.html";
        return;
    }

    const data = JSON.parse(raw);
    document.getElementById("loading").innerText = "Analysis Complete";

    // ✅ FIX 1: correct data path
    const followers = Number(data.input.followers || 0);
    const following = Number(data.input.following || 0);
    const age = Number(data.input.age || 0);

    // ❌ REMOVE your manual risk calculation
    // ✅ FIX 2: use stored risk instead
    const risk = Number(data.output.riskScore || 0);

    // ✅ UI update
    document.getElementById("followers").innerText = followers;
    document.getElementById("following").innerText = following;
    document.getElementById("age").innerText = age;
    document.getElementById("risk").innerText = risk + "%";

    // ✅ FIX 3: reasons from storage (NOT recalculated)
    const reasonsList = document.getElementById("reasons");
    reasonsList.innerHTML = "";

    (data.reasons || []).forEach(r => {
        const li = document.createElement("li");
        li.innerText = r;
        reasonsList.appendChild(li);
    });

    // charts (only if Chart.js loaded)
    if (typeof Chart === "undefined") {
        console.error("Chart.js not loaded");
        return;
    }

    // ✅ donut chart (unchanged logic, just working now)
    new Chart(document.getElementById("donutChart"), {
        type: "doughnut",
        data: {
            labels: ["Safe", "Risk"],
            datasets: [{
                data: [100 - risk, risk],
                backgroundColor: ["#00ff99", "#ff3b3b"]
            }]
        },
        options: {
    responsive: true,
    maintainAspectRatio: true,  // ✅ CHANGE THIS
    cutout: "70%"
}
    });

    // ❌ REMOVE duplicate chart outside DOMContentLoaded
    // ✅ KEEP ONLY THIS ONE INSIDE

    new Chart(document.getElementById("barChart"), {
        type: "bar",
        data: {
            labels: ["Followers", "Following"],
            datasets: [{
                label: "Engagement",
                data: [followers, following],
                backgroundColor: ["#00f2ff", "#00ff88"]
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

});