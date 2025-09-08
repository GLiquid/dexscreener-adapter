# Algebra Integral DEX Screener Adapter

HTTP adapter for integrating Algebra Integral with DEX Screener. Supports multiple chains and protocol versions.

## Features

- ✅ **RPC Only**: Uses exclusively RPC nodes (Infura), no dependency on The Graph
- ✅ **Multi-chain**: Support for Ethereum, Polygon, Arbitrum, Base
- ✅ **Concentrated Liquidity**: Full support for Algebra Integral concentrated liquidity
- ✅ **Multiple Versions**: Support for different Algebra protocol versions
- ✅ **Auto Pool Discovery**: Automatic pool discovery via Factory events
- ✅ **DEX Screener API**: Full compliance with DEX Screener specification

## Architecture

```
app/
├── api/              # FastAPI endpoints
├── config/           # Application configuration  
├── models/           # Pydantic models
├── services/         # Business logic
│   ├── web3_service.py        # Web3 connections
│   ├── pool_discovery.py      # Pool discovery via Factory
│   ├── event_service.py       # Event fetching and parsing
│   └── serializer_service.py  # DEX Screener format conversion
└── utils/            # ABI and helper functions
```

## Installation

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
# Edit the .env file:
nano .env
```

Required settings in `.env`:
```env
INFURA_API_KEY=your_actual_infura_api_key_here
ETHEREUM_FACTORY_V1=0x1a3c9B1d2F0529D97f2afC5136Cc23e58f1FD35B
POLYGON_FACTORY_V1=0x411b0fAcC3489691f28ad58c47006AF5E3Ab3A28
# Add other factory addresses as needed
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

According to [DEX Screener Adapter Specification](https://dexscreener.notion.site/DEX-Screener-Adapter-Specs-cc1223cdf6e74a7799599106b65dcd0e):

### 1. Latest Block
```
GET /latest-block
```
Returns the latest available block.

### 2. Asset Information  
```
GET /asset?id={token_address}
```
Token information by its address.

### 3. Pair Information
```
GET /pair?id={pool_address}  
```
Trading pair/pool information.

### 4. Events
```
GET /events?fromBlock={n}&toBlock={n}&network={optional}
```
Swap, liquidity add/remove events in the specified block range.

### 5. Health Check
```
GET /health
```
Network connection status.

## Usage Examples

### Get latest block:
```bash
curl http://localhost:8000/latest-block
```

### Get token information (WETH):
```bash
curl "http://localhost:8000/asset?id=0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
```

### Get events for the last 100 blocks:
```bash
curl "http://localhost:8000/events?fromBlock=18700000&toBlock=18700100"
```

## Supported Networks

- **Ethereum** (Chain ID: 1)
- **Polygon** (Chain ID: 137) 
- **Arbitrum** (Chain ID: 42161)
- **Base** (Chain ID: 8453)

## How Pool Discovery Works

1. **Factory Events**: Scans `PoolCreated` events from known Factory contracts
2. **Incremental Discovery**: Periodically scans new blocks to discover new pools
3. **Caching**: Caches discovered pools for improved performance

## Algebra Integral Events

Supported event types:
- **Swap**: Token exchanges in pools  
- **Mint**: Liquidity addition (join events)
- **Burn**: Liquidity removal (exit events)

## Development

### Run tests:
```bash
pytest tests/
```

### Project structure:
- `main.py` - FastAPI application entry point
- `app/` - Main application code
- `tests/` - Unit tests
- `requirements.txt` - Python dependencies
- `.env.example` - Configuration example

## Troubleshooting

### RPC connection errors:
- Check that INFURA_API_KEY is correct
- Ensure you have access to the required networks in Infura

### Pools not being discovered:
- Ensure Factory addresses are configured correctly for each network
- Check that you're using the correct protocol versions

### Slow performance:
- Reduce block range in `/events` requests
- Configure Redis for caching (optional)

## Production Configuration

For production environments, it's recommended to:

1. **Use dedicated RPC nodes** instead of Infura for better performance
2. **Configure Redis** for caching
3. **Set up monitoring** and alerting
4. **Use reverse proxy** (nginx) 
5. **Configure logging** and rotation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Create a Pull Request

## License

MIT License
