from typing import Optional, Dict, List, Union
from pydantic import BaseModel


class Block(BaseModel):
    blockNumber: int
    blockTimestamp: int
    metadata: Optional[Dict[str, str]] = None


class Asset(BaseModel):
    id: str
    name: str
    symbol: str
    totalSupply: Optional[Union[str, int]] = None
    circulatingSupply: Optional[Union[str, int]] = None
    coinGeckoId: Optional[str] = None
    coinMarketCapId: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class Pool(BaseModel):
    id: str
    name: str
    assetIds: List[str]
    pairIds: List[str]
    metadata: Optional[Dict[str, str]] = None


class Pair(BaseModel):
    id: str
    dexKey: str
    asset0Id: str
    asset1Id: str
    createdAtBlockNumber: Optional[int] = None
    createdAtBlockTimestamp: Optional[int] = None
    createdAtTxnId: Optional[str] = None
    creator: Optional[str] = None
    feeBps: Optional[int] = None
    metadata: Optional[Dict[str, str]] = None


class Reserves(BaseModel):
    asset0: Union[str, float]
    asset1: Union[str, float]


class SwapEvent(BaseModel):
    eventType: str = "swap"
    txnId: str
    txnIndex: int
    eventIndex: int
    maker: str
    pairId: str
    asset0In: Optional[Union[str, float]] = None
    asset1In: Optional[Union[str, float]] = None
    asset0Out: Optional[Union[str, float]] = None
    asset1Out: Optional[Union[str, float]] = None
    priceNative: Union[str, float]
    reserves: Optional[Reserves] = None
    metadata: Optional[Dict[str, str]] = None


class JoinExitEvent(BaseModel):
    eventType: str  # "join" or "exit"
    txnId: str
    txnIndex: int
    eventIndex: int
    maker: str
    pairId: str
    amount0: Union[str, float]
    amount1: Union[str, float]
    reserves: Optional[Reserves] = None
    metadata: Optional[Dict[str, str]] = None


class EventWithBlock(BaseModel):
    block: Block


class SwapEventWithBlock(EventWithBlock, SwapEvent):
    pass


class JoinExitEventWithBlock(EventWithBlock, JoinExitEvent):
    pass


# Response models
class LatestBlockResponse(BaseModel):
    block: Block


class AssetResponse(BaseModel):
    asset: Asset


class PairResponse(BaseModel):
    pair: Pair


class EventsResponse(BaseModel):
    events: List[Union[SwapEventWithBlock, JoinExitEventWithBlock]]
