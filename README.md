# DeepJudge Legal Search Client

A production-ready Python client for DeepJudge legal knowledge search API with an installable mobile web app for iPhones.

## Features

### Core Features
- **Firm Knowledge Search** - Search legal knowledge with matter-aware filters
- **Grey Area Analysis** - Identify unsettled law and conflicting precedents
- **Risk Assessment** - Analyze potential legal exposure and consequences
- **Defense Strategy Research** - Discover case law supporting legal defense arguments
- **Compliance Optimization** - Structure activities within legal boundaries

### Mobile App Features
- **Installable on iPhone** - Open in Safari and use Add to Home Screen
- **PWA Assets** - Manifest, service worker, and iPhone app icon support
- **Mobile-first UI** - Touch-friendly forms for search and analysis
- **No API Key in the Browser** - Requests go through the Python backend

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Quick Start

### Python client

```python
from deepjudge_client import DeepJudgeClient

client = DeepJudgeClient(api_key="your_enterprise_api_key")
results = client.search_firm_knowledge(
    query="indemnification clause precedent",
    matter_id="M-10294"
)
```

### iPhone-ready web app

```bash
export DEEPJUDGE_API_KEY=your_enterprise_api_key
python -m deepjudge_client --host 0.0.0.0 --port 8000
```

By default, `python -m deepjudge_client` binds to `127.0.0.1`; only use `--host 0.0.0.0` on a trusted local network when you need to open the app from your iPhone.

Then open the app in Safari on your iPhone and choose **Share → Add to Home Screen**. If you started the server with `--host 0.0.0.0`, open `http://<your-computer-lan-ip>:8000` (not `http://0.0.0.0:8000`). The built-in server is intended for development and local testing only; for production, deploy the WSGI app behind a production-grade WSGI server and HTTPS reverse proxy because full PWA features require HTTPS.

## Configuration

Create a `.env` file based on `.env.example`:

```bash
DEEPJUDGE_API_KEY=your_enterprise_api_key
DEEPJUDGE_BASE_URL=https://api.deepjudge.ai/v1
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

## Running Tests

```bash
python -m unittest discover -s tests
```

## License

MIT License - see LICENSE file for details
