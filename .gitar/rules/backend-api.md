# Backend API Rules

- Keep the browser client free of the DeepJudge API key; requests must stay proxied through the Python backend.
- Preserve the current HTTP surface: `GET /`, `POST /api/search`, and `POST /api/analyze`.
- Validate JSON input and return structured JSON errors for invalid requests.
- Keep the mobile web app installable on iPhone by preserving the manifest, service worker, and touch icon assets.
- Prefer minimal changes to the existing WSGI app and `DeepJudgeClient` behavior.
