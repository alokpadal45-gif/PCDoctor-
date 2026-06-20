// This file handles all button clicks and live stat updates.
// It talks to the Flask backend and shows results on each card.


// Called when the user clicks Diagnose on any card.
function diagnose(button) {
    var card = button.closest(".problem-card");
    var problemId = card.getAttribute("data-id");
    var resultDiv = card.querySelector(".card-result");

    showResult(resultDiv, "loading", "Running diagnostic check...");
    disableButtons(card, true);

    fetch("/diagnose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ problem_id: problemId })
    })
    .then(function(response) {
        // Check the response is actually JSON before parsing
        var contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            throw new Error("Server returned an unexpected response. Check the terminal for errors.");
        }
        return response.json();
    })
    .then(function(data) {
        var text = data.message + "\n\n" + (data.details || []).join("\n");
        showResult(resultDiv, "status-" + data.status, text);
        disableButtons(card, false);
    })
    .catch(function(error) {
        showResult(resultDiv, "status-warning", "Error: " + error.message);
        disableButtons(card, false);
    });
}


// Called when the user clicks Fix on any card.
function fix(button) {
    var card = button.closest(".problem-card");
    var problemId = card.getAttribute("data-id");
    var resultDiv = card.querySelector(".card-result");

    showResult(resultDiv, "loading", "Applying fix...");
    disableButtons(card, true);

    fetch("/fix", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ problem_id: problemId })
    })
    .then(function(response) {
        var contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            throw new Error("Server returned an unexpected response. Check the terminal for errors.");
        }
        return response.json();
    })
    .then(function(data) {
        var statusClass = data.success ? "status-success" : "status-failed";
        var text = data.message + "\n\n" + (data.steps || []).join("\n");
        showResult(resultDiv, statusClass, text);
        disableButtons(card, false);
    })
    .catch(function(error) {
        showResult(resultDiv, "status-warning", "Error: " + error.message);
        disableButtons(card, false);
    });
}


// Show the result box on a card with the right colour class.
function showResult(resultDiv, statusClass, text) {
    resultDiv.className = "card-result " + statusClass;
    resultDiv.textContent = text;
}


// Disable or enable both buttons on a card to stop double clicks.
function disableButtons(card, disabled) {
    card.querySelectorAll("button").forEach(function(btn) {
        btn.disabled = disabled;
    });
}


// Refresh the live stats bar every 5 seconds.
function refreshStats() {
    fetch("/system_stats")
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        document.getElementById("cpu-stat").textContent    = data.cpu_percent + "%";
        document.getElementById("ram-stat").textContent    = data.ram_percent + "%";
        document.getElementById("disk-stat").textContent   = data.disk_percent + "%";

        if (data.battery_percent !== null && data.battery_percent !== undefined) {
            document.getElementById("battery-stat").textContent = data.battery_percent + "%";
        }
        if (data.temperature_c !== null && data.temperature_c !== undefined) {
            document.getElementById("temp-stat").textContent = data.temperature_c + " C";
        }
    })
    .catch(function() {
        // If stats refresh fails just keep the old numbers showing
    });
}

setInterval(refreshStats, 5000);