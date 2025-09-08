import asyncio
import logging
from typing import Dict, List, Optional, Set
from app.services.web3_service import web3_manager
from app.config import settings
from app.utils import ALGEBRA_FACTORY_ABI, ALGEBRA_V1_EVENTS, normalize_address
from app.models import AlgebraPool

logger = logging.getLogger(__name__)


class PoolDiscoveryService:
    """Service for discovering Algebra pools via Factory events"""
    
    def __init__(self):
        self._discovered_pools: Dict[str, Set[str]] = {}  # network -> set of pool addresses
        self._pool_cache: Dict[str, AlgebraPool] = {}  # pool_address -> pool data
    
    async def discover_pools(self, network: str, from_block: int = 0, 
                           to_block: Optional[int] = None) -> List[str]:
        """
        Discover all pools created by Factory contracts
        Returns list of pool addresses
        """
        if network not in self._discovered_pools:
            self._discovered_pools[network] = set()
        
        # Get all factory addresses for this network
        factory_addresses = []
        for version in ["v1", "v2"]:
            factory_addr = settings.get_factory_address(network, version)
            if factory_addr:
                factory_addresses.append((factory_addr, version))
        
        if not factory_addresses:
            logger.warning(f"No factory addresses configured for {network}")
            return []
        
        w3 = web3_manager.get_web3(network)
        if not w3:
            logger.error(f"No Web3 connection for {network}")
            return []
        
        if to_block is None:
            to_block = w3.eth.block_number
        
        new_pools = []
        
        for factory_address, version in factory_addresses:
            try:
                # Get PoolCreated events
                pool_created_signature = ALGEBRA_V1_EVENTS["PoolCreated"]  # Same for v1 and v2
                
                filter_params = {
                    "fromBlock": from_block,
                    "toBlock": to_block,
                    "address": factory_address,
                    "topics": [pool_created_signature]
                }
                
                logs = web3_manager.get_logs(network, filter_params)
                
                for log in logs:
                    try:
                        # Decode log data
                        pool_address = self._decode_pool_created_event(log, network, version)
                        if pool_address and pool_address not in self._discovered_pools[network]:
                            self._discovered_pools[network].add(pool_address)
                            new_pools.append(pool_address)
                            logger.info(f"Discovered new pool: {pool_address} on {network}")
                    
                    except Exception as e:
                        logger.error(f"Error decoding pool creation event: {e}")
                        continue
            
            except Exception as e:
                logger.error(f"Error fetching pool creation events from {factory_address}: {e}")
                continue
        
        return new_pools
    
    def _decode_pool_created_event(self, log: dict, network: str, version: str) -> Optional[str]:
        """Decode PoolCreated event to extract pool address"""
        try:
            # For Algebra, the pool address is typically in the data field
            # and token addresses in indexed topics
            
            topics = log.get("topics", [])
            data = log.get("data", "")
            
            if len(topics) >= 3:
                # topics[0] = event signature
                # topics[1] = token0 (indexed)
                # topics[2] = token1 (indexed)
                # data contains pool address
                
                token0 = "0x" + topics[1].hex()[-40:]  # Extract address from topic
                token1 = "0x" + topics[2].hex()[-40:]
                
                # Pool address is in data (assuming it's the first 32 bytes)
                pool_address = "0x" + data[2:42] if len(data) >= 42 else None
                
                if pool_address:
                    pool_address = normalize_address(pool_address)
                    
                    # Cache pool info
                    pool_info = AlgebraPool(
                        address=pool_address,
                        token0=normalize_address(token0),
                        token1=normalize_address(token1),
                        fee=0,  # Will be fetched separately if needed
                        tick_spacing=60,  # Default for Algebra
                        created_at_block=log.get("blockNumber"),
                        created_at_tx=log.get("transactionHash"),
                        network=network,
                        version=version
                    )
                    
                    self._pool_cache[pool_address] = pool_info
                    return pool_address
        
        except Exception as e:
            logger.error(f"Error decoding pool created event: {e}")
        
        return None
    
    def get_discovered_pools(self, network: str) -> List[str]:
        """Get all discovered pools for network"""
        return list(self._discovered_pools.get(network, set()))
    
    def get_pool_info(self, pool_address: str) -> Optional[AlgebraPool]:
        """Get cached pool info"""
        return self._pool_cache.get(pool_address)
    
    async def ensure_pools_discovered(self, network: str, up_to_block: Optional[int] = None):
        """Ensure all pools are discovered up to specified block"""
        if network not in self._discovered_pools:
            # First time discovery - scan from beginning
            await self.discover_pools(network, from_block=0, to_block=up_to_block)
        else:
            # Incremental discovery - scan recent blocks only
            w3 = web3_manager.get_web3(network)
            if w3:
                current_block = up_to_block or w3.eth.block_number
                # Scan last 1000 blocks for new pools
                from_block = max(0, current_block - 1000)
                await self.discover_pools(network, from_block=from_block, to_block=current_block)


# Global pool discovery service
pool_discovery_service = PoolDiscoveryService()
