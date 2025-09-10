from typing import Optional
from pydantic import BaseModel, ConfigDict


class BaseModelWithConfig(BaseModel):
    model_config = ConfigDict(exclude_none=True)


class Token(BaseModelWithConfig):
    """Internal model for ERC-20 token data"""
    address: str
    name: str
    symbol: str
    decimals: int
    total_supply: Optional[int] = None
    network: str


class AlgebraPool(BaseModelWithConfig):
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


class AlgebraPoolWithTokens(BaseModelWithConfig):
    """Extended pool model with full token information"""
    address: str
    token0: Token
    token1: Token
    fee: int
    tick_spacing: int
    created_at_block: Optional[int] = None
    created_at_timestamp: Optional[int] = None
    created_at_tx: Optional[str] = None
    creator: Optional[str] = None
    network: str
    version: Optional[str] = None


class AlgebraSwap(BaseModelWithConfig):
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
    amount0: float
    amount1: float
    sqrt_price_x96: float
    liquidity: int
    tick: int
    network: str
    # Token information included from subgraph
    token0: Token
    token1: Token
    pool_fee: int
    # Optional reserves fields (for V2 subgraphs) - in decimal format
    reserves0: Optional[float] = None
    reserves1: Optional[float] = None


class AlgebraMint(BaseModelWithConfig):
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
    amount0: float
    amount1: float
    tick_lower: int
    tick_upper: int
    amount: int  # liquidity amount
    network: str
    # Token information included from subgraph
    token0: Token
    token1: Token
    pool_fee: int
    # Optional reserves fields (for V2 subgraphs) - in decimal format
    reserves0: Optional[float] = None
    reserves1: Optional[float] = None


class AlgebraBurn(BaseModelWithConfig):
    """Internal model for burn event (remove liquidity)"""
    tx_hash: str
    tx_index: int
    log_index: int
    block_number: int
    block_timestamp: int
    pool_address: str
    owner: str
    tx_origin: str  # Transaction origin (from field)
    amount0: float
    amount1: float
    tick_lower: int
    tick_upper: int
    amount: int  # liquidity amount
    network: str
    # Token information included from subgraph
    token0: Token
    token1: Token
    pool_fee: int
    # Optional reserves fields (for V2 subgraphs) - in decimal format
    reserves0: Optional[float] = None
    reserves1: Optional[float] = None
