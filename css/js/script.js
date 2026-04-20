document.addEventListener("DOMContentLoaded", () => {

    const btn = document.getElementById("analyzeBtn");

    if (!btn) {
        console.error("Button not found");
        return;
    }

    btn.addEventListener("click", function () {

        const followers = Number(document.getElementById("followers").value);
        const following = Number(document.getElementById("following").value);
        const age = Number(document.getElementById("age").value);

        // ✅ FIXED LINE
        if (followers <= 0 || following <= 0 || age <= 0) {
            alert("Fill all fields correctly");
            return;
        }

        let risk = 0;
        let reasons = [];

        if (following > followers) {
            risk += 40;
            reasons.push("Following > Followers");
        }

        if (age < 30) {
            risk += 30;
            reasons.push("New account");
        }

        if (followers < 100) {
            risk += 20;
            reasons.push("Low followers");
        }

        if (risk > 100) risk = 100;

        const data = {
            input: { followers, following, age },
            output: { riskScore: risk },
            reasons
        };

        localStorage.setItem("analysisData", JSON.stringify(data));

        console.log("DATA SAVED:", data);

        window.location.href = "dashboard.html";
    });

});