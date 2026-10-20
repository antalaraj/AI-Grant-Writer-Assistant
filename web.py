import os
import logging
import warnings
from flask import Flask, render_template, request, jsonify

os.environ.setdefault("LITELLM_LOG", "CRITICAL")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("PYTHONWARNINGS", "ignore")
logging.basicConfig(level=logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.INFO)
# Keep runtime warnings visible while diagnosing deployment issues.

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", os.urandom(32).hex())


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/loading-fragment")
def loading_fragment():
    return render_template("loading.html")


@app.route("/run-grant-writer", methods=["POST"])
def run_grant_writer():
    data = request.get_json(silent=True) or {}
    org_type = str(data.get("org_type", "")).strip()
    mission = str(data.get("mission", "")).strip()

    if not org_type or not mission:
        return jsonify({"error": "Please fill in all fields."}), 400

    if len(org_type) > 200 or len(mission) > 5000:
        return jsonify({"error": "Organization type or mission is too long."}), 400

    # Groq is required for drafting. Gemini is an optional second-pass validator;
    # grant_workflow.py already degrades gracefully when Gemini is unavailable.
    missing_keys = [
        key for key in ("GROQ_API_KEY",)
        if not os.getenv(key)
    ]
    if missing_keys:
        return jsonify({
            "error": "Server configuration is incomplete.",
            "details": "Configure GROQ_API_KEY in Vercel project settings. GEMINI_API_KEY enables optional independent validation."
        }), 503

    try:
        # Import lazily so the home page still loads if AI dependencies or
        # provider credentials have a configuration problem.
        from grant_workflow import generate_grant_report
        report = generate_grant_report(org_type, mission)
        return render_template("result.html", raw_output=report)
    except Exception as exc:
        # Keep full traceback in Vercel logs; do not expose provider responses to visitors.
        app.logger.exception("Grant report generation failed (%s)", type(exc).__name__)
        return jsonify({
            "error": "The grant-writing workflow failed.",
            "details": "Check the Vercel function logs and verify your API keys and dependency versions."
        }), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
