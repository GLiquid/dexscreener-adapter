from typing import Optional, Dict, List, Union
from pydantic import BaseModel, ConfigDict


class BaseModelWithConfig(BaseModel):
    model_config = ConfigDict(exclude_none=True)


class Block(BaseModelWithConfig):
    blockNumber: int
    blockTimestamp: int
    metadata: Optional[Dict[str, str]] = None


class Asset(BaseModelWithConfig):
    id: str
    name: str
    symbol: str
    totalSupply: Optional[Union[str, int]] = None
    circulatingSupply: Optional[Union[str, int]] = None
    coinGeckoId: Optional[str] = None
    coinMarketCapId: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class Pool(BaseModelWithConfig):
    id: str
    name: str
    assetIds: List[str]
    pairIds: List[str]
    metadata: Optional[Dict[str, str]] = None


class Pair(BaseModelWithConfig):
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


class Reserves(BaseModelWithConfig):
    asset0: Union[str, float]
    asset1: Union[str, float]


class SwapEvent(BaseModelWithConfig):
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


class JoinExitEvent(BaseModelWithConfig):
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


class EventWithBlock(BaseModelWithConfig):
    block: Block


class SwapEventWithBlock(EventWithBlock, SwapEvent):
    pass


class JoinExitEventWithBlock(EventWithBlock, JoinExitEvent):
    pass


# Response models
class LatestBlockResponse(BaseModelWithConfig):
    block: Block


class AssetResponse(BaseModelWithConfig):
    asset: Asset


class PairResponse(BaseModelWithConfig):
    pair: Pair


class EventsResponse(BaseModelWithConfig):
    events: List[Union[SwapEventWithBlock, JoinExitEventWithBlock]]
