# Run Mobile App

Use this procedure when asked to run or verify the installable DeepJudge mobile app.

1. Ensure dependencies are installed with `pip install -r requirements.txt` and `pip install -e .`.
2. Start the app with `python -m deepjudge_client --host 0.0.0.0 --port 8000`.
3. Verify the home page loads and that `/manifest.webmanifest` and `/service-worker.js` are reachable.
4. If iPhone install behavior is being checked, confirm the app is opened in Safari and added through Share → Add to Home Screen.
