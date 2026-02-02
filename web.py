import os
import sys
import subprocess
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-prod'

@app.route('/')
def index():
    """Renders the main input form."""
    return render_template('index.html')

@app.route('/loading-fragment')
def loading_fragment():
    """Returns the HTML for the loading spinner (fetched via JS)."""
    return render_template('loading.html')

@app.route('/run-grant-writer', methods=['POST'])
def run_grant_writer():
    """
    Executes app.py using subprocess.
    Passes user input via STDIN.
    Captures STDOUT/STDERR.
    """
    data = request.json
    org_type = data.get('org_type', '').strip()
    mission = data.get('mission', '').strip()

    if not org_type or not mission:
        return jsonify({'error': 'Please fill in all fields.'}), 400

    # Prepare input string (matches the input() calls in app.py)
    # app.py asks for Org Type first, then Mission.
    input_str = f"{org_type}\n{mission}\n"

    try:
        # Run app.py as a subprocess
        # python -u forces unbuffered binary stdout
        process = subprocess.Popen(
            [sys.executable, '-u', 'app.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Text mode for easier string handling
            cwd=os.getcwd()  # Ensure we run in the correct directory
        )

        # Communicate sends input and waits for termination
        stdout, stderr = process.communicate(input=input_str)

        if process.returncode != 0:
            # Check if it was a crash or just a non-zero exit
            return jsonify({
                'error': 'The agent encountered an error.',
                'details': stderr or stdout
            }), 500

        # Render the result template with the captured output
        # We pass the raw markdown to be rendered by JS on the frontend
        return render_template('result.html', raw_output=stdout)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Running on port 5000 by default
    print("Starting Web Interface for AI Grant Writer...")
    app.run(debug=True, port=5000)