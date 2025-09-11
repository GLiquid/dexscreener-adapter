import logging
import aiohttp

from typing import Dict, List, Optional
from app.config import settings
from app.models import Token, AlgebraSwap, AlgebraMint, AlgebraBurn, AlgebraPoolWithTokens
from app.utils import normalize_address

logger = logging.getLogger(__name__)


class SubgraphService:
    """Service for fetching data from Algebra Integral subgraphs with reserves support"""
    
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
    
    def _get_swap_query_fields(self) -> str:
        """Get swap query fields with reserves included"""
        return """
                id
                pool {
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
                }
                sender
                origin
                recipient
                amount0
                amount1
                price
                liquidity
                tick
                reserves0
                reserves1"""
    
    def _get_mint_query_fields(self) -> str:
        """Get mint query fields with reserves included"""
        return """
                id
                pool {
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
                }
                owner
                sender
                origin
                amount0
                amount1
                tickLower
                tickUpper
                amount
                reserves0
                reserves1"""
    
    def _get_burn_query_fields(self) -> str:
        """Get burn query fields with reserves included"""
        return """
                id
                pool {
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
                }
                owner
                origin
                amount0
                amount1
                tickLower
                tickUpper
                amount
                reserves0
                reserves1"""
    
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
    
    async def get_latest_transaction(self, network: str) -> Optional[Dict]:
        """Get latest transaction from subgraph"""
        query = """
        query GetLatestTransaction {
            transactions(
                first: 1,
                orderBy: blockNumber,
                orderDirection: desc
            ) {
                id
                index
                blockNumber
                timestamp
            }
        }
        """
        
        result = await self.query_subgraph(network, query)
        if result and "transactions" in result and result["transactions"]:
            tx_data = result["transactions"][0]
            return {
                "blockNumber": int(tx_data["blockNumber"]),
                "blockTimestamp": int(tx_data["timestamp"])
            }
        return None
    
    async def get_factory_address(self, network: str) -> Optional[str]:
        """Get factory address from subgraph"""
        query = """
        query GetFactory {
            factories(first: 1) {
                id
            }
        }
        """
        
        result = await self.query_subgraph(network, query)
        if result and "factories" in result and result["factories"]:
            return result["factories"][0]["id"]
        return None

    
    async def get_pool_with_tokens(self, network: str, pool_address: str) -> Optional[AlgebraPoolWithTokens]:
        """Get pool information with full token details in one query"""
        query = """
        query GetPoolWithTokens($poolId: ID!) {
            pool(id: $poolId) {
                id
                token0 {
                    id
                    symbol
                    name
                    decimals
                    totalSupply
                }
                token1 {
                    id
                    symbol
                    name
                    decimals
                    totalSupply
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
        
        variables = {"poolId": pool_address.lower()}
        result = await self.query_subgraph(network, query, variables)
        
        if result and "pool" in result and result["pool"]:
            pool_data = result["pool"]
            try:
                from app.models import AlgebraPoolWithTokens, Token
                
                # Create token objects
                token0 = Token(
                    address=normalize_address(pool_data["token0"]["id"]),
                    name=pool_data["token0"].get("name", ""),
                    symbol=pool_data["token0"].get("symbol", ""),
                    decimals=int(pool_data["token0"].get("decimals", 18)),
                    total_supply=int(float(pool_data["token0"].get("totalSupply", 0))) if pool_data["token0"].get("totalSupply") else None,
                    network=network
                )
                
                token1 = Token(
                    address=normalize_address(pool_data["token1"]["id"]),
                    name=pool_data["token1"].get("name", ""),
                    symbol=pool_data["token1"].get("symbol", ""),
                    decimals=int(pool_data["token1"].get("decimals", 18)),
                    total_supply=int(float(pool_data["token1"].get("totalSupply", 0))) if pool_data["token1"].get("totalSupply") else None,
                    network=network
                )
                
                return AlgebraPoolWithTokens(
                    address=normalize_address(pool_data["id"]),
                    token0=token0,
                    token1=token1,
                    fee=int(pool_data.get("fee", 0)),
                    tick_spacing=int(pool_data.get("tickSpacing", 60)),
                    created_at_block=int(pool_data.get("createdAtBlockNumber", 0)) if pool_data.get("createdAtBlockNumber") else None,
                    created_at_timestamp=int(pool_data.get("createdAtTimestamp", 0)) if pool_data.get("createdAtTimestamp") else None,
                    network=network
                )
            except Exception as e:
                logger.error(f"Error parsing pool with tokens data: {e}")
        
        return None
    

    
    async def get_all_events(self, network: str, from_block: int, to_block: int, first: int = 1000) -> Dict[str, List]:
        """Get all events (swaps, mints, burns) from subgraph using cursor-based pagination"""
        # Build query fields for each event type (reserves included by default)
        swap_fields = self._get_swap_query_fields().strip()
        mint_fields = self._get_mint_query_fields().strip()
        burn_fields = self._get_burn_query_fields().strip()

        
        query = f"""
        query GetAllEvents($fromBlock: Int!, $toBlock: Int!, $first: Int!, $lastId: ID) {{
            transactions(
                where: {{
                    blockNumber_gte: $fromBlock,
                    blockNumber_lte: $toBlock,
                    id_gt: $lastId
                }},
                first: $first,
                orderBy: id,
                orderDirection: asc
            ) {{
                id
                index
                blockNumber
                timestamp
                swaps {{{swap_fields}
                }}
                mints {{{mint_fields}
                }}
                burns {{{burn_fields}
                }}
            }}
        }}
        """
        
        all_swaps = []
        all_mints = []
        all_burns = []
        last_id = ""
        
        while True:
            variables = {
                "fromBlock": from_block,
                "toBlock": to_block,
                "first": first,
                "lastId": last_id
            }
            result = await self.query_subgraph(network, query, variables)
            batch = result["transactions"] if result and "transactions" in result else []
            if not batch:
                break
            
            for tx_data in batch:
                tx_id = tx_data["id"]
                block_number = int(tx_data["blockNumber"])
                timestamp = int(tx_data["timestamp"])
                
                # Process swaps
                for swap_data in tx_data.get("swaps", []):
                    try:
                        # Extract token information from pool data
                        pool_data = swap_data["pool"]
                        token0 = Token(
                            address=normalize_address(pool_data["token0"]["id"]),
                            name=pool_data["token0"].get("name", ""),
                            symbol=pool_data["token0"].get("symbol", ""),
                            decimals=int(pool_data["token0"].get("decimals", 18)),
                            network=network
                        )
                        token1 = Token(
                            address=normalize_address(pool_data["token1"]["id"]),
                            name=pool_data["token1"].get("name", ""),
                            symbol=pool_data["token1"].get("symbol", ""),
                            decimals=int(pool_data["token1"].get("decimals", 18)),
                            network=network
                        )
                        swap = AlgebraSwap(
                            tx_hash=tx_id,
                            tx_index=tx_data.get("index", 0),
                            log_index=int(swap_data.get("logIndex", 0)),
                            block_number=block_number,
                            block_timestamp=timestamp,
                            pool_address=normalize_address(pool_data["id"]),
                            sender=normalize_address(swap_data["sender"]),
                            recipient=normalize_address(swap_data["recipient"]),
                            tx_origin=normalize_address(swap_data["origin"]),
                            amount0=float(swap_data["amount0"]),
                            amount1=float(swap_data["amount1"]),
                            sqrt_price_x96=float(swap_data["price"]),
                            liquidity=int(swap_data["liquidity"]),
                            tick=int(swap_data["tick"]),
                            network=network,
                            token0=token0,
                            token1=token1,
                            pool_fee=int(pool_data.get("fee", 0)),
                            # Include reserves if available (already in decimal format)
                            reserves0=float(swap_data["reserves0"]) if swap_data.get("reserves0") else None,
                            reserves1=float(swap_data["reserves1"]) if swap_data.get("reserves1") else None
                        )
                        all_swaps.append(swap)
                    except Exception as e:
                        logger.error(f"Error parsing swap data: {e}")
                        continue
                # Process mints
                for mint_data in tx_data.get("mints", []):
                    try:
                        # Extract token information from pool data
                        pool_data = mint_data["pool"]
                        token0 = Token(
                            address=normalize_address(pool_data["token0"]["id"]),
                            name=pool_data["token0"].get("name", ""),
                            symbol=pool_data["token0"].get("symbol", ""),
                            decimals=int(pool_data["token0"].get("decimals", 18)),
                            network=network
                        )
                        token1 = Token(
                            address=normalize_address(pool_data["token1"]["id"]),
                            name=pool_data["token1"].get("name", ""),
                            symbol=pool_data["token1"].get("symbol", ""),
                            decimals=int(pool_data["token1"].get("decimals", 18)),
                            network=network
                        )
                        
                        mint = AlgebraMint(
                            tx_hash=tx_id,
                            tx_index=tx_data.get("index", 0),
                            log_index=int(mint_data.get("logIndex", 0)),
                            block_number=block_number,
                            block_timestamp=timestamp,
                            pool_address=normalize_address(pool_data["id"]),
                            owner=normalize_address(mint_data["owner"]),
                            sender=normalize_address(mint_data["sender"]),
                            tx_origin=normalize_address(mint_data["origin"]),
                            amount0=float(mint_data["amount0"]),
                            amount1=float(mint_data["amount1"]),
                            tick_lower=int(mint_data["tickLower"]),
                            tick_upper=int(mint_data["tickUpper"]),
                            amount=int(float(mint_data["amount"])),
                            network=network,
                            token0=token0,
                            token1=token1,
                            pool_fee=int(pool_data.get("fee", 0)),
                            # Include reserves if available (already in decimal format)
                            reserves0=float(mint_data["reserves0"]) if mint_data.get("reserves0") else None,
                            reserves1=float(mint_data["reserves1"]) if mint_data.get("reserves1") else None
                        )
                        all_mints.append(mint)
                    except Exception as e:
                        logger.error(f"Error parsing mint data: {e}")
                        continue
                # Process burns
                for burn_data in tx_data.get("burns", []):
                    try:
                        # Extract token information from pool data
                        pool_data = burn_data["pool"]
                        token0 = Token(
                            address=normalize_address(pool_data["token0"]["id"]),
                            name=pool_data["token0"].get("name", ""),
                            symbol=pool_data["token0"].get("symbol", ""),
                            decimals=int(pool_data["token0"].get("decimals", 18)),
                            network=network
                        )
                        token1 = Token(
                            address=normalize_address(pool_data["token1"]["id"]),
                            name=pool_data["token1"].get("name", ""),
                            symbol=pool_data["token1"].get("symbol", ""),
                            decimals=int(pool_data["token1"].get("decimals", 18)),
                            network=network
                        )
                        
                        burn = AlgebraBurn(
                            tx_hash=tx_id,
                            tx_index=tx_data.get("index", 0),
                            log_index=int(burn_data.get("logIndex", 0)),
                            block_number=block_number,
                            block_timestamp=timestamp,
                            pool_address=normalize_address(pool_data["id"]),
                            owner=normalize_address(burn_data["owner"]),
                            tx_origin=normalize_address(burn_data["origin"]),
                            amount0=float(float(burn_data["amount0"])),
                            amount1=float(float(burn_data["amount1"])),
                            tick_lower=int(burn_data["tickLower"]),
                            tick_upper=int(burn_data["tickUpper"]),
                            amount=int(float(burn_data["amount"])),
                            network=network,
                            token0=token0,
                            token1=token1,
                            pool_fee=int(pool_data.get("fee", 0)),
                            # Include reserves if available (already in decimal format)
                            reserves0=float(burn_data["reserves0"]) if burn_data.get("reserves0") else None,
                            reserves1=float(burn_data["reserves1"]) if burn_data.get("reserves1") else None
                        )
                        all_burns.append(burn)
                    except Exception as e:
                        logger.error(f"Error parsing burn data: {e}")
                        continue
            last_id = batch[-1]["id"]
            if len(batch) < first:
                break
        return {
            "swaps": all_swaps,
            "mints": all_mints,
            "burns": all_burns
        }
    
    async def get_token(self, network: str, token_address: str) -> Optional[Token]:
        """Get token information from subgraph (simplified version for compatibility)"""
        query = """
        query GetToken($tokenId: ID!) {
            token(id: $tokenId) {
                id
                symbol
                name
                decimals
                totalSupply
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
    



# Global subgraph service instance
subgraph_service = SubgraphService()
