import logging
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from app.config import settings
from app.models import AlgebraPool, Token, AlgebraSwap, AlgebraMint, AlgebraBurn
from app.utils import normalize_address

logger = logging.getLogger(__name__)


class SubgraphService:
    """Service for fetching data from Algebra Integral subgraphs"""
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session
    
    async def close(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def query_subgraph(self, network: str, query: str, variables: Optional[Dict] = None) -> Optional[Dict]:
        """Execute GraphQL query against subgraph"""
        subgraph_url = settings.get_subgraph_url(network)
        if not subgraph_url:
            logger.error(f"No subgraph URL configured for network: {network}")
            return None
        
        session = await self._get_session()
        
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        try:
            async with session.post(subgraph_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if "errors" in data:
                        logger.error(f"Subgraph query errors: {data['errors']}")
                        return None
                    return data.get("data")
                else:
                    logger.error(f"Subgraph request failed with status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error querying subgraph for {network}: {e}")
            return None
    
    async def get_latest_block(self, network: str) -> Optional[Dict]:
        """Get latest block from subgraph"""
        query = """
        query GetLatestBlock {
            _meta {
                block {
                    number
                    timestamp
                }
            }
        }
        """
        
        result = await self.query_subgraph(network, query)
        if result and "_meta" in result:
            block_data = result["_meta"]["block"]
            return {
                "blockNumber": int(block_data["number"]),
                "blockTimestamp": int(block_data["timestamp"])
            }
        return None
    
    async def get_pools(self, network: str, first: int = 1000, skip: int = 0) -> List[AlgebraPool]:
        """Get pools from subgraph"""
        query = """
        query GetPools($first: Int!, $skip: Int!) {
            pools(first: $first, skip: $skip, orderBy: createdAtTimestamp, orderDirection: desc) {
                id
                token0 {
                    id
                    symbol
                    name
                    decimals
                }
                token1 {
                    id
                    symbol
                    name
                    decimals
                }
                fee
                tickSpacing
                createdAtTimestamp
                createdAtBlockNumber
                txCount
                totalValueLockedUSD
                volumeUSD
            }
        }
        """
        
        variables = {"first": first, "skip": skip}
        result = await self.query_subgraph(network, query, variables)
        
        pools = []
        if result and "pools" in result:
            for pool_data in result["pools"]:
                try:
                    pool = AlgebraPool(
                        address=normalize_address(pool_data["id"]),
                        token0=normalize_address(pool_data["token0"]["id"]),
                        token1=normalize_address(pool_data["token1"]["id"]),
                        fee=int(pool_data.get("fee", 0)),
                        tick_spacing=int(pool_data.get("tickSpacing", 60)),
                        created_at_block=int(pool_data.get("createdAtBlockNumber", 0)) if pool_data.get("createdAtBlockNumber") else None,
                        created_at_timestamp=int(pool_data.get("createdAtTimestamp", 0)) if pool_data.get("createdAtTimestamp") else None,
                        network=network
                        # version omitted - not critical for current implementation
                    )
                    pools.append(pool)
                except Exception as e:
                    logger.error(f"Error parsing pool data: {e}")
                    continue
        
        return pools
    
    async def get_token(self, network: str, token_address: str) -> Optional[Token]:
        """Get token information from subgraph"""
        query = """
        query GetToken($tokenId: ID!) {
            token(id: $tokenId) {
                id
                symbol
                name
                decimals
                totalSupply
                totalValueLocked
                totalValueLockedUSD
            }
        }
        """
        
        variables = {"tokenId": token_address.lower()}
        result = await self.query_subgraph(network, query, variables)
        
        if result and "token" in result and result["token"]:
            token_data = result["token"]
            try:
                return Token(
                    address=normalize_address(token_data["id"]),
                    name=token_data.get("name", ""),
                    symbol=token_data.get("symbol", ""),
                    decimals=int(token_data.get("decimals", 18)),
                    total_supply=int(float(token_data.get("totalSupply", 0))) if token_data.get("totalSupply") else None,
                    network=network
                )
            except Exception as e:
                logger.error(f"Error parsing token data: {e}")
        
        return None
    
    async def get_swaps(self, network: str, from_block: int, to_block: int, first: int = 1000) -> List[AlgebraSwap]:
        """Get swap events from subgraph using cursor-based pagination"""
        query = """
        query GetSwaps($fromBlock: Int!, $toBlock: Int!, $first: Int!, $lastId: ID) {
            swaps(
                where: {
                    blockNumber_gte: $fromBlock,
                    blockNumber_lte: $toBlock,
                    id_gt: $lastId
                },
                first: $first,
                orderBy: id,
                orderDirection: asc
            ) {
                id
                transaction {
                    id
                    blockNumber
                    timestamp
                    from
                }
                pool {
                    id
                }
                sender
                recipient
                amount0
                amount1
                sqrtPriceX96
                liquidity
                tick
                logIndex
            }
        }
        """
        swaps = []
        last_id = ""
        while True:
            variables = {
                "fromBlock": from_block,
                "toBlock": to_block,
                "first": first,
                "lastId": last_id
            }
            result = await self.query_subgraph(network, query, variables)
            batch = result["swaps"] if result and "swaps" in result else []
            if not batch:
                break
            for swap_data in batch:
                try:
                    tx_data = swap_data["transaction"]
                    swap = AlgebraSwap(
                        tx_hash=tx_data["id"],
                        tx_index=0,
                        log_index=int(swap_data.get("logIndex", 0)),
                        block_number=int(tx_data["blockNumber"]),
                        block_timestamp=int(tx_data["timestamp"]),
                        pool_address=normalize_address(swap_data["pool"]["id"]),
                        sender=normalize_address(swap_data["sender"]),
                        recipient=normalize_address(swap_data["recipient"]),
                        tx_origin=normalize_address(tx_data["from"]),
                        amount0=int(float(swap_data["amount0"])),
                        amount1=int(float(swap_data["amount1"])),
                        sqrt_price_x96=int(swap_data["sqrtPriceX96"]),
                        liquidity=int(swap_data["liquidity"]),
                        tick=int(swap_data["tick"]),
                        network=network
                    )
                    swaps.append(swap)
                except Exception as e:
                    logger.error(f"Error parsing swap data: {e}")
                    continue
            last_id = batch[-1]["id"]
            if len(batch) < first:
                break
        return swaps
    
    async def get_mints(self, network: str, from_block: int, to_block: int, first: int = 1000) -> List[AlgebraMint]:
        """Get mint events from subgraph using cursor-based pagination"""
        query = """
        query GetMints($fromBlock: Int!, $toBlock: Int!, $first: Int!, $lastId: ID) {
            mints(
                where: {
                    blockNumber_gte: $fromBlock,
                    blockNumber_lte: $toBlock,
                    id_gt: $lastId
                },
                first: $first,
                orderBy: id,
                orderDirection: asc
            ) {
                id
                transaction {
                    id
                    blockNumber
                    timestamp
                    from
                }
                pool {
                    id
                }
                owner
                sender
                amount0
                amount1
                tickLower
                tickUpper
                amount
                logIndex
            }
        }
        """
        mints = []
        last_id = ""
        while True:
            variables = {
                "fromBlock": from_block,
                "toBlock": to_block,
                "first": first,
                "lastId": last_id
            }
            result = await self.query_subgraph(network, query, variables)
            batch = result["mints"] if result and "mints" in result else []
            if not batch:
                break
            for mint_data in batch:
                try:
                    tx_data = mint_data["transaction"]
                    mint = AlgebraMint(
                        tx_hash=tx_data["id"],
                        tx_index=0,
                        log_index=int(mint_data.get("logIndex", 0)),
                        block_number=int(tx_data["blockNumber"]),
                        block_timestamp=int(tx_data["timestamp"]),
                        pool_address=normalize_address(mint_data["pool"]["id"]),
                        owner=normalize_address(mint_data["owner"]),
                        sender=normalize_address(mint_data["sender"]),
                        tx_origin=normalize_address(tx_data["from"]),
                        amount0=int(float(mint_data["amount0"])),
                        amount1=int(float(mint_data["amount1"])),
                        tick_lower=int(mint_data["tickLower"]),
                        tick_upper=int(mint_data["tickUpper"]),
                        amount=int(float(mint_data["amount"])),
                        network=network
                    )
                    mints.append(mint)
                except Exception as e:
                    logger.error(f"Error parsing mint data: {e}")
                    continue
            last_id = batch[-1]["id"]
            if len(batch) < first:
                break
        return mints
    
    async def get_burns(self, network: str, from_block: int, to_block: int, first: int = 1000) -> List[AlgebraBurn]:
        """Get burn events from subgraph using cursor-based pagination"""
        query = """
        query GetBurns($fromBlock: Int!, $toBlock: Int!, $first: Int!, $lastId: ID) {
            burns(
                where: {
                    blockNumber_gte: $fromBlock,
                    blockNumber_lte: $toBlock,
                    id_gt: $lastId
                },
                first: $first,
                orderBy: id,
                orderDirection: asc
            ) {
                id
                transaction {
                    id
                    blockNumber
                    timestamp
                    from
                }
                pool {
                    id
                }
                owner
                amount0
                amount1
                tickLower
                tickUpper
                amount
                logIndex
            }
        }
        """
        burns = []
        last_id = ""
        while True:
            variables = {
                "fromBlock": from_block,
                "toBlock": to_block,
                "first": first,
                "lastId": last_id
            }
            result = await self.query_subgraph(network, query, variables)
            batch = result["burns"] if result and "burns" in result else []
            if not batch:
                break
            for burn_data in batch:
                try:
                    tx_data = burn_data["transaction"]
                    burn = AlgebraBurn(
                        tx_hash=tx_data["id"],
                        tx_index=0,
                        log_index=int(burn_data.get("logIndex", 0)),
                        block_number=int(tx_data["blockNumber"]),
                        block_timestamp=int(tx_data["timestamp"]),
                        pool_address=normalize_address(burn_data["pool"]["id"]),
                        owner=normalize_address(burn_data["owner"]),
                        tx_origin=normalize_address(tx_data["from"]),
                        amount0=int(float(burn_data["amount0"])),
                        amount1=int(float(burn_data["amount1"])),
                        tick_lower=int(burn_data["tickLower"]),
                        tick_upper=int(burn_data["tickUpper"]),
                        amount=int(float(burn_data["amount"])),
                        network=network
                    )
                    burns.append(burn)
                except Exception as e:
                    logger.error(f"Error parsing burn data: {e}")
                    continue
            last_id = batch[-1]["id"]
            if len(batch) < first:
                break
        return burns


# Global subgraph service instance
subgraph_service = SubgraphService()
