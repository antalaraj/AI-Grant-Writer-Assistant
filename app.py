"""Vercel Flask entry point. The agent workflow lives in grant_workflow.py."""
from web import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
