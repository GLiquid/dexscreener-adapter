import logging
from typing import List, Optional, Dict, Tuple
from app.services.web3_service import web3_manager
from app.services.pool_discovery import pool_discovery_service
from app.utils import (
    ALGEBRA_V1_EVENTS, ALGEBRA_V2_EVENTS, ERC20_ABI,
    calculate_price_from_sqrt_price, format_amount, normalize_address
)
from app.models import AlgebraSwap, AlgebraMint, AlgebraBurn, AlgebraToken
from app.config import settings

logger = logging.getLogger(__name__)


class EventService:
    """Service for fetching and processing Algebra events"""
    
    def __init__(self):
        self._token_cache: Dict[str, AlgebraToken] = {}  # address -> token info
    
    async def get_swap_events(self, network: str, from_block: int, 
                            to_block: int) -> List[AlgebraSwap]:
        """Get all swap events from Algebra pools in block range"""
        
        # Ensure pools are discovered
        await pool_discovery_service.ensure_pools_discovered(network, to_block)
        pool_addresses = pool_discovery_service.get_discovered_pools(network)
        
        if not pool_addresses:
            logger.warning(f"No pools discovered for {network}")
            return []
        
        swaps = []
        
        # Get swap events from all pools
        for pool_address in pool_addresses:
            pool_swaps = await self._get_pool_swap_events(
                network, pool_address, from_block, to_block
            )
            swaps.extend(pool_swaps)
        
        # Sort by block number and transaction index
        swaps.sort(key=lambda x: (x.block_number, x.tx_index, x.log_index))
        
        return swaps
    
    async def get_mint_events(self, network: str, from_block: int, 
                            to_block: int) -> List[AlgebraMint]:
        """Get all mint events (add liquidity) from Algebra pools"""
        
        await pool_discovery_service.ensure_pools_discovered(network, to_block)
        pool_addresses = pool_discovery_service.get_discovered_pools(network)
        
        mints = []
        
        for pool_address in pool_addresses:
            pool_mints = await self._get_pool_mint_events(
                network, pool_address, from_block, to_block
            )
            mints.extend(pool_mints)
        
        mints.sort(key=lambda x: (x.block_number, x.tx_index, x.log_index))
        
        return mints
    
    async def get_burn_events(self, network: str, from_block: int, 
                            to_block: int) -> List[AlgebraBurn]:
        """Get all burn events (remove liquidity) from Algebra pools"""
        
        await pool_discovery_service.ensure_pools_discovered(network, to_block)
        pool_addresses = pool_discovery_service.get_discovered_pools(network)
        
        burns = []
        
        for pool_address in pool_addresses:
            pool_burns = await self._get_pool_burn_events(
                network, pool_address, from_block, to_block
            )
            burns.extend(pool_burns)
        
        burns.sort(key=lambda x: (x.block_number, x.tx_index, x.log_index))
        
        return burns
    
    async def _get_pool_swap_events(self, network: str, pool_address: str, 
                                  from_block: int, to_block: int) -> List[AlgebraSwap]:
        """Get swap events for specific pool"""
        
        # Determine protocol version for this pool
        pool_info = pool_discovery_service.get_pool_info(pool_address)
        version = pool_info.version if pool_info else "v1"
        
        event_signature = ALGEBRA_V1_EVENTS["Swap"] if version == "v1" else ALGEBRA_V2_EVENTS["Swap"]
        
        filter_params = {
            "fromBlock": from_block,
            "toBlock": to_block,
            "address": pool_address,
            "topics": [event_signature]
        }
        
        logs = web3_manager.get_logs(network, filter_params)
        swaps = []
        
        for log in logs:
            try:
                swap = self._decode_swap_event(log, network)
                if swap:
                    swaps.append(swap)
            except Exception as e:
                logger.error(f"Error decoding swap event: {e}")
                continue
        
        return swaps
    
    async def _get_pool_mint_events(self, network: str, pool_address: str,
                                  from_block: int, to_block: int) -> List[AlgebraMint]:
        """Get mint events for specific pool"""
        
        pool_info = pool_discovery_service.get_pool_info(pool_address)
        version = pool_info.version if pool_info else "v1"
        
        event_signature = ALGEBRA_V1_EVENTS["Mint"] if version == "v1" else ALGEBRA_V2_EVENTS["Mint"]
        
        filter_params = {
            "fromBlock": from_block,
            "toBlock": to_block,
            "address": pool_address,
            "topics": [event_signature]
        }
        
        logs = web3_manager.get_logs(network, filter_params)
        mints = []
        
        for log in logs:
            try:
                mint = self._decode_mint_event(log, network)
                if mint:
                    mints.append(mint)
            except Exception as e:
                logger.error(f"Error decoding mint event: {e}")
                continue
        
        return mints
    
    async def _get_pool_burn_events(self, network: str, pool_address: str,
                                  from_block: int, to_block: int) -> List[AlgebraBurn]:
        """Get burn events for specific pool"""
        
        pool_info = pool_discovery_service.get_pool_info(pool_address)
        version = pool_info.version if pool_info else "v1"
        
        event_signature = ALGEBRA_V1_EVENTS["Burn"] if version == "v1" else ALGEBRA_V2_EVENTS["Burn"]
        
        filter_params = {
            "fromBlock": from_block,
            "toBlock": to_block,
            "address": pool_address,
            "topics": [event_signature]
        }
        
        logs = web3_manager.get_logs(network, filter_params)
        burns = []
        
        for log in logs:
            try:
                burn = self._decode_burn_event(log, network)
                if burn:
                    burns.append(burn)
            except Exception as e:
                logger.error(f"Error decoding burn event: {e}")
                continue
        
        return burns
    
    def _decode_swap_event(self, log: dict, network: str) -> Optional[AlgebraSwap]:
        """Decode swap event log"""
        try:
            # Get transaction receipt for additional data
            tx_receipt = web3_manager.get_transaction_receipt(network, log["transactionHash"])
            if not tx_receipt:
                return None
            
            # Extract data from log
            topics = log.get("topics", [])
            data = log.get("data", "")
            
            # Decode based on Algebra Swap event structure
            # Swap(address indexed sender, address indexed recipient, int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick)
            
            if len(topics) >= 3:
                sender = "0x" + topics[1].hex()[-40:]
                recipient = "0x" + topics[2].hex()[-40:]
                
                # Decode data field (amount0, amount1, sqrtPriceX96, liquidity, tick)
                w3 = web3_manager.get_web3(network)
                decoded = w3.codec.decode(
                    ["int256", "int256", "uint160", "uint128", "int24"],
                    bytes.fromhex(data[2:])
                )
                
                amount0, amount1, sqrt_price_x96, liquidity, tick = decoded
                
                return AlgebraSwap(
                    tx_hash=log["transactionHash"],
                    tx_index=tx_receipt["transactionIndex"],
                    log_index=log["logIndex"],
                    block_number=log["blockNumber"],
                    block_timestamp=0,  # Will be filled by caller
                    pool_address=normalize_address(log["address"]),
                    sender=normalize_address(sender),
                    recipient=normalize_address(recipient),
                    amount0=amount0,
                    amount1=amount1,
                    sqrt_price_x96=sqrt_price_x96,
                    liquidity=liquidity,
                    tick=tick,
                    network=network
                )
        
        except Exception as e:
            logger.error(f"Error decoding swap event: {e}")
        
        return None
    
    def _decode_mint_event(self, log: dict, network: str) -> Optional[AlgebraMint]:
        """Decode mint event log"""
        try:
            tx_receipt = web3_manager.get_transaction_receipt(network, log["transactionHash"])
            if not tx_receipt:
                return None
            
            topics = log.get("topics", [])
            data = log.get("data", "")
            
            # Mint event structure varies by version, but generally:
            # Mint(address sender, address indexed owner, int24 indexed bottomTick, int24 indexed topTick, uint128 liquidityAmount, uint256 amount0, uint256 amount1)
            
            if len(topics) >= 4:
                owner = "0x" + topics[1].hex()[-40:]
                bottom_tick = int.from_bytes(topics[2], "big", signed=True)
                top_tick = int.from_bytes(topics[3], "big", signed=True)
                
                # Decode data (sender, liquidityAmount, amount0, amount1)
                w3 = web3_manager.get_web3(network)
                decoded = w3.codec.decode(
                    ["address", "uint128", "uint256", "uint256"],
                    bytes.fromhex(data[2:])
                )
                
                sender, liquidity_amount, amount0, amount1 = decoded
                
                return AlgebraMint(
                    tx_hash=log["transactionHash"],
                    tx_index=tx_receipt["transactionIndex"],
                    log_index=log["logIndex"],
                    block_number=log["blockNumber"],
                    block_timestamp=0,
                    pool_address=normalize_address(log["address"]),
                    owner=normalize_address(owner),
                    sender=normalize_address(sender),
                    amount0=amount0,
                    amount1=amount1,
                    tick_lower=bottom_tick,
                    tick_upper=top_tick,
                    amount=liquidity_amount,
                    network=network
                )
        
        except Exception as e:
            logger.error(f"Error decoding mint event: {e}")
        
        return None
    
    def _decode_burn_event(self, log: dict, network: str) -> Optional[AlgebraBurn]:
        """Decode burn event log"""
        try:
            tx_receipt = web3_manager.get_transaction_receipt(network, log["transactionHash"])
            if not tx_receipt:
                return None
            
            topics = log.get("topics", [])
            data = log.get("data", "")
            
            # Burn event: Burn(address indexed owner, int24 indexed bottomTick, int24 indexed topTick, uint128 liquidityAmount, uint256 amount0, uint256 amount1)
            
            if len(topics) >= 4:
                owner = "0x" + topics[1].hex()[-40:]
                bottom_tick = int.from_bytes(topics[2], "big", signed=True)
                top_tick = int.from_bytes(topics[3], "big", signed=True)
                
                # Decode data (liquidityAmount, amount0, amount1)
                w3 = web3_manager.get_web3(network)
                decoded = w3.codec.decode(
                    ["uint128", "uint256", "uint256"],
                    bytes.fromhex(data[2:])
                )
                
                liquidity_amount, amount0, amount1 = decoded
                
                return AlgebraBurn(
                    tx_hash=log["transactionHash"],
                    tx_index=tx_receipt["transactionIndex"],
                    log_index=log["logIndex"],
                    block_number=log["blockNumber"],
                    block_timestamp=0,
                    pool_address=normalize_address(log["address"]),
                    owner=normalize_address(owner),
                    amount0=amount0,
                    amount1=amount1,
                    tick_lower=bottom_tick,
                    tick_upper=top_tick,
                    amount=liquidity_amount,
                    network=network
                )
        
        except Exception as e:
            logger.error(f"Error decoding burn event: {e}")
        
        return None
    
    async def get_token_info(self, network: str, token_address: str) -> Optional[AlgebraToken]:
        """Get token information from contract"""
        
        cache_key = f"{network}:{token_address}"
        if cache_key in self._token_cache:
            return self._token_cache[cache_key]
        
        try:
            name = web3_manager.call_contract_function(
                network, token_address, ERC20_ABI, "name"
            )
            symbol = web3_manager.call_contract_function(
                network, token_address, ERC20_ABI, "symbol"
            )
            decimals = web3_manager.call_contract_function(
                network, token_address, ERC20_ABI, "decimals"
            )
            total_supply = web3_manager.call_contract_function(
                network, token_address, ERC20_ABI, "totalSupply"
            )
            
            if name and symbol and decimals is not None:
                token = AlgebraToken(
                    address=normalize_address(token_address),
                    name=name,
                    symbol=symbol,
                    decimals=decimals,
                    total_supply=total_supply,
                    network=network
                )
                
                self._token_cache[cache_key] = token
                return token
        
        except Exception as e:
            logger.error(f"Error getting token info for {token_address}: {e}")
        
        return None


# Global event service
event_service = EventService()
