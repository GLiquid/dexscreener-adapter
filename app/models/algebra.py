from typing import Optional, Dict, Any
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
    version: str


class AlgebraToken(BaseModel):
    """Internal model for token data"""
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
    amount0: int
    amount1: int
    sqrt_price_x96: int
    liquidity: int
    tick: int
    network: str


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
    amount0: int
    amount1: int
    tick_lower: int
    tick_upper: int
    amount: int  # liquidity amount
    network: str


class AlgebraBurn(BaseModel):
    """Internal model for burn event (remove liquidity)"""
    tx_hash: str
    tx_index: int
    log_index: int
    block_number: int
    block_timestamp: int
    pool_address: str
    owner: str
    amount0: int
    amount1: int
    tick_lower: int
    tick_upper: int
    amount: int  # liquidity amount
    network: str


class NetworkInfo(BaseModel):
    """Network configuration"""
    name: str
    chain_id: int
    rpc_url: str
    factory_addresses: Dict[str, str]  # version -> address
    
    
class ProtocolVersion(BaseModel):
    """Protocol version info"""
    version: str
    factory_address: str
    pool_created_event_signature: str
    swap_event_signature: str
    mint_event_signature: str
    burn_event_signature: str
