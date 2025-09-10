# DEX Screener Adapter

Universal HTTP adapter for integrating Algebra DEX protocols with DEX Screener. Supports multiple chains and provides a unified API interface.

## Quick Deployment with Docker

### Prerequisites
- Docker & Docker Compose installed
- 2GB RAM minimum
- Open ports: 80, 443

### Deploy in 3 Steps

1. **Clone & Configure:**
```bash
git clone <repository>
cd dexscreener-adapter
cp .env.example .env
# Edit .env file with your configuration
```

2. **Start Services:**
```bash
docker-compose up -d
```

3. **Test API:**
```bash
# Test health
curl http://localhost/health

# Test endpoints
curl http://localhost/dex/polygon/latest-block
curl http://localhost/dex/ethereum/latest-block
```

## Manual Installation

### Development Setup

1. **Clone and setup environment:**
```bash
git clone <repo>
cd dexscreener-adapter
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configuration:**
```bash
cp .env.example .env
# Edit the .env file with your settings
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

NETWORKS=ethereum,polygon,custom_network
```

## Usage

### Development server:
```bash
python main.py
```

### Production server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Server will be available at: http://localhost:8000

## API Endpoints

All endpoints follow the pattern: `/dex/{network}/{endpoint}`

```

### Development Server Examples
```bash
# Get latest block:
curl http://localhost:8000/dex/ethereum/latest-block

# Get token information (WETH):
curl "http://localhost:8000/dex/ethereum/asset?id=0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

# Get events for the last 100 blocks:
curl "http://localhost:8000/dex/ethereum/events?fromBlock=18700000&toBlock=18700100"
```

## Monitoring & Troubleshooting

### Check Status (Docker)
```bash
# Service status
docker-compose ps

# Logs
docker-compose logs -f dex-adapter
docker-compose logs -f nginx
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart dex-adapter

# Full rebuild
docker-compose down
docker-compose up -d --build
```

## Development

### Development Server
```bash
# Using Python directly
python main.py

# Using uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Tests
```bash
pytest tests/
```
## Production Configuration

### SSL/HTTPS Setup
1. Get SSL certificates (Let's Encrypt recommended)
2. Update `nginx.conf` with SSL configuration
3. Place certificates in `./ssl/` directory

### Production Environment Variables
```env
# Production settings
LOG_LEVEL=WARNING
WORKERS=4

# Security
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
CORS_ORIGINS=https://yourdomain.com

# Performance
CACHE_TTL=300
MAX_CONNECTIONS=100
```
