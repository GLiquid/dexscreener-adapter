"""
Algebra Integral ABI definitions and event signatures
"""

# Factory ABI (for getting pools)
ALGEBRA_FACTORY_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "token0", "type": "address"},
            {"indexed": True, "name": "token1", "type": "address"},
            {"indexed": False, "name": "pool", "type": "address"}
        ],
        "name": "Pool",
        "type": "event"
    }
]

# Pool ABI (for swap and liquidity events)
ALGEBRA_POOL_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": True, "name": "recipient", "type": "address"},
            {"indexed": False, "name": "amount0", "type": "int256"},
            {"indexed": False, "name": "amount1", "type": "int256"},
            {"indexed": False, "name": "sqrtPriceX96", "type": "uint160"},
            {"indexed": False, "name": "liquidity", "type": "uint128"},
            {"indexed": False, "name": "tick", "type": "int24"}
        ],
        "name": "Swap",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "sender", "type": "address"},
            {"indexed": True, "name": "owner", "type": "address"},
            {"indexed": True, "name": "bottomTick", "type": "int24"},
            {"indexed": True, "name": "topTick", "type": "int24"},
            {"indexed": False, "name": "liquidityAmount", "type": "uint128"},
            {"indexed": False, "name": "amount0", "type": "uint256"},
            {"indexed": False, "name": "amount1", "type": "uint256"}
        ],
        "name": "Mint",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "owner", "type": "address"},
            {"indexed": True, "name": "bottomTick", "type": "int24"},
            {"indexed": True, "name": "topTick", "type": "int24"},
            {"indexed": False, "name": "liquidityAmount", "type": "uint128"},
            {"indexed": False, "name": "amount0", "type": "uint256"},
            {"indexed": False, "name": "amount1", "type": "uint256"}
        ],
        "name": "Burn",
        "type": "event"
    }
]

# ERC20 ABI for getting token information
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol", 
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

# Event signatures for different versions
ALGEBRA_V1_EVENTS = {
    "PoolCreated": "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118",
    "Swap": "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67", 
    "Mint": "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde",
    "Burn": "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c"
}

ALGEBRA_V2_EVENTS = {
    "PoolCreated": "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118", 
    "Swap": "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67",
    "Mint": "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde", 
    "Burn": "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c"
}

# Chain IDs
CHAIN_IDS = {
    "ethereum": 1,
    "polygon": 137,
    "arbitrum": 42161,
    "base": 8453
}
