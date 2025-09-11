# DEX Screener Adapter

Adapter for integrating Algebra DEX protocols with DEX Screener. Supports multiple chains and provides a unified API interface.

## Quick Deployment with Docker

### Prerequisites
- Docker & Docker Compose installed
- 2GB RAM minimum
- Open ports: 80, 443

### Deploy in 3 Steps

1. **Configure:**
```bash
cd dexscreener-adapter
cp .env.example .env
# Edit .env file with your configuration
```

2. **Start Services:**
```bash
docker compose up --build -d
```

3. **Test API:**

All endpoints follow the pattern: `/{network}/{endpoint}`

```bash
# Test health
curl http://localhost/health

# Test endpoints
curl http://localhost//polygon/latest-block
curl http://localhost/polygon/asset?id=0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2

```


## Configuration

The adapter uses a flexible configuration system based on environment variables.

### Required Settings in `.env`:
```env
# Networks (comma-separated list)
NETWORKS=ethereum,polygon,arbitrum,base

# Logging
LOG_LEVEL=INFO
```

### Network Configuration
Each network requires a subgraph URL configured with the pattern `{NETWORK}_SUBGRAPH_URL`:

```env
# Default networks (automatically configured if not specified)
ETHEREUM_SUBGRAPH_URL=https://api.thegraph.com/subgraphs/name/cryptoalgebra/algebra-integral-mainnet
POLYGON_SUBGRAPH_URL=https://api.thegraph.com/subgraphs/name/cryptoalgebra/algebra-integral-polygon

NETWORKS=ethereum,polygon
```

### Reserves Support
The adapter automatically detects whether subgraphs support reserves fields. If a subgraph includes reserves data, it will be included in the DEX Screener response. If not, the reserves field will be `null` (backward compatible).
