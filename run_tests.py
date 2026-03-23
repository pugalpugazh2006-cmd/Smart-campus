import subprocess
import time
import sys

print("Starting Flask application...", flush=True)
flask_process = subprocess.Popen([sys.executable, "-m", "flask", "run", "--port=5000"])

# Give Flask time to start
time.sleep(3)

print("\nRunning HTTP Login Test...", flush=True)
test_process = subprocess.run([sys.executable, "test_http_login.py"], capture_output=True, text=True)
print(test_process.stdout)
if test_process.stderr:
    print("Errors:", test_process.stderr)

print("\nShutting down Flask application...", flush=True)
flask_process.terminate()
flask_process.wait()
print("Done.")
