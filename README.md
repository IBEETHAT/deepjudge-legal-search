# DeepJudge Legal Search Client

A production-ready Python client for DeepJudge legal knowledge search API with advanced features for legal research and analysis.

## Features

### Core Features
- **Legal Grey Area Analysis** - Identify unsettled law and conflicting precedents
- **Regulatory Loophole Identification** - Find legitimate gaps in regulations for compliance optimization
- **Risk Assessment** - Analyze potential legal exposure and consequences
- **Defense Strategy Research** - Discover case law supporting legal defense arguments
- **Compliance Optimization** - Structure activities within legal boundaries

### Performance Features
- **Intelligent Caching** - Redis-backed caching for repeated queries
- **Automatic Retries** - Exponential backoff retry logic for failed requests
- **Rate Limiting** - Built-in rate limit handling and throttling
- **Batch Processing** - Efficiently process multiple queries in parallel
- **Connection Pooling** - Optimized HTTP connection management

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from deepjudge_client import DeepJudgeClient

# Initialize client
client = DeepJudgeClient(api_key="your_enterprise_api_key")

# Search firm knowledge
results = client.search_firm_knowledge(
    query="indemnification clause precedent",
    matter_id="M-10294"
)

# Analyze grey areas
from deepjudge_client import GreyAreaAnalyzer
analyzer = GreyAreaAnalyzer(client)
grey_areas = analyzer.analyze(
    topic="contract interpretation",
    jurisdiction="US"
)
```

## Configuration

Create a `.env` file based on `.env.example`:

```bash
DEEPJUDGE_API_KEY=your_enterprise_api_key
DEEPJUDGE_BASE_URL=https://api.deepjudge.ai/v1
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

## License

MIT License - see LICENSE file for details
