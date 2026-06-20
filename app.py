# This is the main file that starts the web server.
# Run this file to launch the PC Doctor application.
# In your terminal: python app.py

from flask import Flask, render_template, request, jsonify
from modules.diagnostics import run_diagnostic
from modules.fixes import apply_fix
from modules.system_info import get_system_info

app = Flask(__name__)


# Home page - loads the main dashboard
@app.route("/")
def index():
    system_info = get_system_info()
    return render_template("index.html", system_info=system_info)


# Called when the user clicks Diagnose on any problem card
@app.route("/diagnose", methods=["POST"])
def diagnose():
    try:
        data = request.get_json()
        problem_id = data.get("problem_id")

        if not problem_id:
            return jsonify({"status": "warning", "message": "No problem ID sent.", "details": [], "can_auto_fix": False})

        result = run_diagnostic(problem_id)
        return jsonify(result)

    except Exception as e:
        # If anything crashes inside the check, return a clean JSON error
        # so the frontend never receives an HTML page by mistake
        return jsonify({"status": "warning", "message": f"Diagnostic error: {str(e)}", "details": [], "can_auto_fix": False})


# Called when the user clicks Fix on any problem card
@app.route("/fix", methods=["POST"])
def fix():
    try:
        data = request.get_json()
        problem_id = data.get("problem_id")

        if not problem_id:
            return jsonify({"success": False, "message": "No problem ID sent.", "steps": []})

        result = apply_fix(problem_id)
        return jsonify(result)

    except Exception as e:
        # Same safety net - always return JSON, never HTML
        return jsonify({"success": False, "message": f"Fix error: {str(e)}", "steps": []})


# Called by JavaScript every few seconds to refresh the live stats bar
@app.route("/system_stats")
def system_stats():
    try:
        return jsonify(get_system_info())
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)