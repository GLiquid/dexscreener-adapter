from typing import Optional
from pydantic import BaseModel


class AlgebraPool(BaseModel):
    """Internal model for Algebra pool data"""
    address: str
    token0: str
    token1: str
    fee: int
    tick_spacing: int
    created_at_block: Optional[int] = None
    created_at_timestamp: Optional[int] = None
    created_at_tx: Optional[str] = None
    creator: Optional[str] = None
    network: str
    version: Optional[str] = None  # Optional - protocol version if needed


class Token(BaseModel):
    """Internal model for ERC-20 token data"""
    address: str
    name: str
    symbol: str
    decimals: int
    total_supply: Optional[int] = None
    network: str


class AlgebraSwap(BaseModel):
    """Internal model for swap event"""
    tx_hash: str
    tx_index: int
    log_index: int
    block_number: int
    block_timestamp: int
    pool_address: str
    sender: str
    recipient: str
    tx_origin: str  # Transaction origin (from field)
    amount0: int
    amount1: int
    sqrt_price_x96: int
    liquidity: int
    tick: int
    network: str
    # Optional reserves fields (for V2 subgraphs) - in decimal format
    reserves0: Optional[float] = None
    reserves1: Optional[float] = None


class AlgebraMint(BaseModel):
    """Internal model for mint event (add liquidity)"""
    tx_hash: str
    tx_index: int
    log_index: int
    block_number: int
    block_timestamp: int
    pool_address: str
    owner: str
    sender: str
    tx_origin: str  # Transaction origin (from field)
    amount0: int
    amount1: int
    tick_lower: int
    tick_upper: int
    amount: int  # liquidity amount
    network: str
    # Optional reserves fields (for V2 subgraphs) - in decimal format
    reserves0: Optional[float] = None
    reserves1: Optional[float] = None


class AlgebraBurn(BaseModel):
    """Internal model for burn event (remove liquidity)"""
    tx_hash: str
    tx_index: int
    log_index: int
    block_number: int
    block_timestamp: int
    pool_address: str
    owner: str
    tx_origin: str  # Transaction origin (from field)
    amount0: int
    amount1: int
    tick_lower: int
    tick_upper: int
    amount: int  # liquidity amount
    network: str
    # Optional reserves fields (for V2 subgraphs) - in decimal format
    reserves0: Optional[float] = None
    reserves1: Optional[float] = None
