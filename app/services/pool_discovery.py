import asyncio
import logging
from typing import Dict, List, Optional, Set
from app.services.subgraph_service import subgraph_service
from app.models import AlgebraPool
from app.utils import normalize_address

logger = logging.getLogger(__name__)


class PoolDiscoveryService:
    """Service for discovering Algebra pools via subgraph"""
    
    def __init__(self):
        self._discovered_pools: Dict[str, Set[str]] = {}  # network -> set of pool addresses
        self._pool_cache: Dict[str, AlgebraPool] = {}  # pool_address -> pool data
    
    async def discover_pools(self, network: str, limit: int = 1000) -> List[str]:
        """
        Discover all pools from subgraph
        Returns list of pool addresses
        """
        if network not in self._discovered_pools:
            self._discovered_pools[network] = set()
        
        new_pools = []
        
        try:
            # Get pools from subgraph
            pools = await subgraph_service.get_pools(network, first=limit)
            
            for pool in pools:
                if pool.address not in self._discovered_pools[network]:
                    self._discovered_pools[network].add(pool.address)
                    self._pool_cache[pool.address] = pool
                    new_pools.append(pool.address)
                    logger.info(f"Discovered pool: {pool.address} on {network}")
                else:
                    # Update cache with latest data
                    self._pool_cache[pool.address] = pool
            
            logger.info(f"Discovered {len(new_pools)} new pools on {network}")
            
        except Exception as e:
            logger.error(f"Error discovering pools from subgraph: {e}")
        
        return new_pools
    
    def get_discovered_pools(self, network: str) -> List[str]:
        """Get all discovered pools for network"""
        return list(self._discovered_pools.get(network, set()))
    
    def get_pool_info(self, pool_address: str) -> Optional[AlgebraPool]:
        """Get cached pool info"""
        return self._pool_cache.get(pool_address)
    
    async def ensure_pools_discovered(self, network: str, limit: int = 1000):
        """Ensure pools are discovered for the network"""
        if network not in self._discovered_pools or len(self._discovered_pools[network]) == 0:
            # First time discovery
            await self.discover_pools(network, limit=limit)
        else:
            # Refresh pool data periodically
            await self.discover_pools(network, limit=limit)
    
    async def get_pool_by_address(self, network: str, pool_address: str) -> Optional[AlgebraPool]:
        """Get specific pool info, fetch from subgraph if not cached"""
        
        # Check cache first
        pool = self.get_pool_info(pool_address)
        if pool:
            return pool
        
        try:
            # Try to get pool info directly from subgraph
            query = """
            query GetPool($poolId: ID!) {
                pool(id: $poolId) {
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
            
            variables = {"poolId": pool_address.lower()}
            result = await subgraph_service.query_subgraph(network, query, variables)
            
            if result and "pool" in result and result["pool"]:
                pool_data = result["pool"]
                pool = AlgebraPool(
                    address=normalize_address(pool_data["id"]),
                    token0=normalize_address(pool_data["token0"]["id"]),
                    token1=normalize_address(pool_data["token1"]["id"]),
                    fee=int(pool_data.get("fee", 0)),
                    tick_spacing=int(pool_data.get("tickSpacing", 60)),
                    created_at_block=int(pool_data.get("createdAtBlockNumber", 0)) if pool_data.get("createdAtBlockNumber") else None,
                    created_at_timestamp=int(pool_data.get("createdAtTimestamp", 0)) if pool_data.get("createdAtTimestamp") else None,
                    network=network
                    # version omitted - not needed for current use case
                )
                
                # Cache the pool
                self._pool_cache[pool_address] = pool
                if network not in self._discovered_pools:
                    self._discovered_pools[network] = set()
                self._discovered_pools[network].add(pool_address)
                
                return pool
        
        except Exception as e:
            logger.error(f"Error fetching pool {pool_address} from subgraph: {e}")
        
        return None


# Global pool discovery service
pool_discovery_service = PoolDiscoveryService()
