# fb_threatexchange

A Python library for ThreatExchange integration.

## Overview

`fb_threatexchange` provides utilities for working with Meta's ThreatExchange platform, enabling you to query, submit, and manage threat intelligence data.

## Installation

### For Development

```bash
# Clone the repository and navigate to the project directory
cd fb_threatexchange

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### For Production Use

```bash
pip install fb_threatexchange
```

## Quick Start

```python
from fb_threatexchange import ThreatExchangeClient, ThreatDescriptor, ThreatIndicator
from fb_threatexchange.models import ThreatType, Status, ShareLevel

# Initialize the client
client = ThreatExchangeClient(
    app_id="your_app_id",
    app_secret="your_app_secret",
)

# Search for threat descriptors
descriptors = client.get_threat_descriptors("malware.example.com")

# Create a new threat indicator
indicator = ThreatIndicator(
    id="ind_123",
    indicator="malicious-domain.com",
    type=ThreatType.MALICIOUS_URL,
)

# Create a threat descriptor
descriptor = ThreatDescriptor(
    id="desc_123",
    indicator=indicator,
    owner_id="your_owner_id",
    status=Status.MALICIOUS,
    share_level=ShareLevel.AMBER,
    description="Known malicious domain",
    tags=["malware", "phishing"],
)

# Submit to ThreatExchange
response = client.submit_descriptor(descriptor)
```

## Features

- **ThreatExchangeClient**: Main client for API interactions
- **ThreatDescriptor**: Model for threat descriptors with metadata
- **ThreatIndicator**: Model for threat indicators (hashes, URLs, etc.)
- **Enums**: `ThreatType`, `ShareLevel`, `Status` for type-safe operations

## Project Structure

```
fb_threatexchange/
├── pyproject.toml          # Project configuration
├── README.md               # This file
├── src/
│   └── fb_threatexchange/
│       ├── __init__.py     # Package exports
│       ├── core.py         # ThreatExchangeClient
│       ├── models.py       # Data models
│       └── py.typed        # PEP 561 marker
└── tests/
    ├── __init__.py
    ├── test_core.py        # Client tests
    └── test_models.py      # Model tests
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fb_threatexchange --cov-report=html

# Run specific test file
pytest tests/test_models.py
```

### Code Formatting

```bash
# Format code with black
black src tests

# Sort imports
isort src tests

# Type checking
mypy src
```

### Linting

```bash
# Run all linters
black --check src tests
isort --check src tests
mypy src
```

## API Reference

### ThreatExchangeClient

The main client for interacting with the ThreatExchange API.

#### Methods

- `get_access_token()`: Generate the access token for authentication
- `get_threat_descriptors(text, limit=100)`: Search for threat descriptors
- `get_threat_indicators(descriptor_id)`: Get indicators for a descriptor
- `submit_descriptor(descriptor)`: Submit a new threat descriptor

### ThreatDescriptor

Represents a threat descriptor with metadata.

#### Attributes

- `id`: Unique identifier
- `indicator`: Associated ThreatIndicator
- `owner_id`: Owner's ID
- `status`: Status enum (MALICIOUS, SUSPICIOUS, etc.)
- `share_level`: ShareLevel enum (WHITE, GREEN, AMBER, RED)
- `description`: Human-readable description
- `tags`: List of tags
- `creation_time`: When the descriptor was created
- `expire_time`: When the descriptor expires

### ThreatIndicator

Represents a specific threat indicator.

#### Attributes

- `id`: Unique identifier
- `indicator`: The actual indicator value (hash, URL, etc.)
- `type`: ThreatType enum
- `creation_time`: When the indicator was created
- `last_updated`: When the indicator was last updated

## License

MIT License

## Links

- [ThreatExchange Documentation](https://developers.facebook.com/docs/threat-exchange)
- [ThreatExchange GitHub](https://github.com/facebook/ThreatExchange)

