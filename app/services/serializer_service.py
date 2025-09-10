import logging
from typing import List, Optional, Dict, Union
from app.models import (
    Block, Asset, Pair, SwapEventWithBlock, JoinExitEventWithBlock,
    AlgebraSwap, AlgebraMint, AlgebraBurn, Token, AlgebraPoolWithTokens,
    Reserves
)
from app.services.event_service import event_service
from app.services.subgraph_service import subgraph_service
from app.utils import (
    format_amount, calculate_price_from_sqrt_price, normalize_address
)

logger = logging.getLogger(__name__)


class SerializerService:
    """Service for converting Algebra data to DEX Screener format"""
    
    def __init__(self):
        self.dex_key = "algebra"
    
    async def serialize_block(self, network: str, block_number: int) -> Block:
        """Convert block data to DEX Screener format"""
        
        try:
            # Get latest block info from subgraph
            latest_block = await subgraph_service.get_latest_block(network)
            
            # If specific block requested and it's different from latest, try to get timestamp
            if latest_block and latest_block["number"] >= block_number:
                # Use subgraph's latest block timestamp as approximation
                # For exact timestamp, would need additional subgraph query or RPC call
                return Block(
                    blockNumber=block_number,
                    blockTimestamp=latest_block["timestamp"]
                )
            else:
                # Return current block
                return Block(
                    blockNumber=latest_block["number"] if latest_block else block_number,
                    blockTimestamp=latest_block["timestamp"] if latest_block else 0
                )
        
        except Exception as e:
            logger.error(f"Error fetching block data from subgraph: {e}")
            return Block(
                blockNumber=block_number,
                blockTimestamp=0
            )
    
    async def serialize_asset(self, network: str, token_address: str) -> Asset:
        """Convert token data to DEX Screener format"""
        
        token = await event_service.get_token_info(network, token_address)
        if not token:
            raise ValueError(f"Could not fetch token info for {token_address}")
        
        # Build asset data, only include fields that have values
        asset_data = {
            "id": token.address,
            "name": token.name,
            "symbol": token.symbol,
            "metadata": {
                "network": network,
                "decimals": str(token.decimals)
            }
        }
        
        # Only add totalSupply if it has a value
        if token.total_supply:
            total_supply_formatted = format_amount(token.total_supply, token.decimals)
            if total_supply_formatted:
                asset_data["totalSupply"] = total_supply_formatted
        
        return Asset(**asset_data)
    
    async def serialize_pair(self, network: str, pool_address: str) -> Pair:
        """Convert pool data to DEX Screener format"""
        
        pool_info = await subgraph_service.get_pool_with_tokens(network, pool_address)
        if not pool_info:
            raise ValueError(f"Could not find pool info for {pool_address}")
        
        # Now we have all token information from one query
        token0 = pool_info.token0
        token1 = pool_info.token1
        
        # Calculate fee in bps (Algebra typically uses different fee structures)
        fee_bps = pool_info.fee // 100 if pool_info.fee else None
        
        # Build pair data, only include fields that have values
        pair_data = {
            "id": pool_info.address,
            "dexKey": f"{self.dex_key}-{network}",
            "asset0Id": token0.address,
            "asset1Id": token1.address,
            "metadata": {
                "network": network,
                "tickSpacing": str(pool_info.tick_spacing),
                "token0Symbol": token0.symbol,
                "token1Symbol": token1.symbol,
                "token0Decimals": str(token0.decimals),
                "token1Decimals": str(token1.decimals)
            }
        }
        
        # Only add optional fields if they have values
        if pool_info.created_at_block is not None:
            pair_data["createdAtBlockNumber"] = pool_info.created_at_block
        if pool_info.created_at_timestamp is not None:
            pair_data["createdAtBlockTimestamp"] = pool_info.created_at_timestamp
        if hasattr(pool_info, 'created_at_tx') and pool_info.created_at_tx is not None:
            pair_data["createdAtTxnId"] = pool_info.created_at_tx
        if hasattr(pool_info, 'creator') and pool_info.creator is not None:
            pair_data["creator"] = pool_info.creator
        if fee_bps is not None:
            pair_data["feeBps"] = fee_bps
        
        return Pair(**pair_data)
    
    async def serialize_swap_event(self, swap: AlgebraSwap) -> SwapEventWithBlock:
        """Convert Algebra swap to DEX Screener swap event"""
        
        # Format amounts - use absolute values for in/out amounts
        amount0_abs = abs(swap.amount0)
        amount1_abs = abs(swap.amount1)
        
        # Determine direction (which token is in vs out) - format as strings without scientific notation
        asset0_in = f"{amount0_abs:.18f}".rstrip('0').rstrip('.') if swap.amount0 > 0 else None
        asset0_out = f"{amount0_abs:.18f}".rstrip('0').rstrip('.') if swap.amount0 < 0 else None
        asset1_in = f"{amount1_abs:.18f}".rstrip('0').rstrip('.') if swap.amount1 > 0 else None
        asset1_out = f"{amount1_abs:.18f}".rstrip('0').rstrip('.') if swap.amount1 < 0 else None
        
        # Calculate price (price of token0 in terms of token1) - always positive, formatted as string
        price_raw = abs(swap.amount0 / swap.amount1) if swap.amount1 != 0 else 0
        price_native = f"{price_raw:.18f}".rstrip('0').rstrip('.')
        
        # Include reserves if available from subgraph
        reserves = None
        if swap.reserves0 is not None and swap.reserves1 is not None:
            # Reserves come in decimal format from subgraph (e.g., 0.0001)
            # Convert to string without scientific notation for DEX Screener API
            reserves = Reserves(
                asset0=f"{swap.reserves0:.18f}".rstrip('0').rstrip('.'),
                asset1=f"{swap.reserves1:.18f}".rstrip('0').rstrip('.')
            )
        
        # Build swap event data, only include fields that have values
        swap_data = {
            "block": Block(
                blockNumber=swap.block_number,
                blockTimestamp=swap.block_timestamp
            ),
            "eventType": "swap",
            "txnId": swap.tx_hash,
            "txnIndex": swap.tx_index,
            "eventIndex": swap.log_index,
            "maker": swap.tx_origin,
            "pairId": swap.pool_address,
            "priceNative": price_native,
            "metadata": {
                "network": swap.network
            }
        }
        
        # Only add asset amounts if they have values
        if asset0_in is not None:
            swap_data["asset0In"] = asset0_in
        if asset0_out is not None:
            swap_data["asset0Out"] = asset0_out
        if asset1_in is not None:
            swap_data["asset1In"] = asset1_in
        if asset1_out is not None:
            swap_data["asset1Out"] = asset1_out
        if reserves is not None:
            swap_data["reserves"] = reserves
        
        return SwapEventWithBlock(**swap_data)
    
    async def serialize_mint_event(self, mint: AlgebraMint) -> JoinExitEventWithBlock:
        """Convert Algebra mint to DEX Screener join event"""
        
        
        # Include reserves if available from subgraph
        reserves = None
        if mint.reserves0 is not None and mint.reserves1 is not None:
            # Reserves come in decimal format from subgraph (e.g., 0.0001)
            # Convert to string without scientific notation for DEX Screener API
            reserves = Reserves(
                asset0=f"{mint.reserves0:.18f}".rstrip('0').rstrip('.'),
                asset1=f"{mint.reserves1:.18f}".rstrip('0').rstrip('.')
            )
        
        # Build mint event data, only include fields that have values
        mint_data = {
            "block": Block(
                blockNumber=mint.block_number,
                blockTimestamp=mint.block_timestamp
            ),
            "eventType": "join",
            "txnId": mint.tx_hash,
            "txnIndex": mint.tx_index,
            "eventIndex": mint.log_index,
            "maker": mint.tx_origin,
            "pairId": mint.pool_address,
            "amount0": f"{mint.amount0:.18f}".rstrip('0').rstrip('.'),
            "amount1": f"{mint.amount1:.18f}".rstrip('0').rstrip('.'),
            "metadata": {
                "network": mint.network
            }
        }
        
        # Only add reserves if available
        if reserves is not None:
            mint_data["reserves"] = reserves
        
        return JoinExitEventWithBlock(**mint_data)
    
    async def serialize_burn_event(self, burn: AlgebraBurn) -> JoinExitEventWithBlock:
        """Convert Algebra burn to DEX Screener exit event"""
        
        # Include reserves if available from subgraph
        reserves = None
        if burn.reserves0 is not None and burn.reserves1 is not None:
            # Reserves come in decimal format from subgraph (e.g., 0.0001)
            # Convert to string without scientific notation for DEX Screener API
            reserves = Reserves(
                asset0=f"{burn.reserves0:.18f}".rstrip('0').rstrip('.'),
                asset1=f"{burn.reserves1:.18f}".rstrip('0').rstrip('.')
            )
        
        # Build burn event data, only include fields that have values
        burn_data = {
            "block": Block(
                blockNumber=burn.block_number,
                blockTimestamp=burn.block_timestamp
            ),
            "eventType": "exit",
            "txnId": burn.tx_hash,
            "txnIndex": burn.tx_index,
            "eventIndex": burn.log_index,
            "maker": burn.tx_origin,
            "pairId": burn.pool_address,
            "amount0": f"{burn.amount0:.18f}".rstrip('0').rstrip('.'),
            "amount1": f"{burn.amount1:.18f}".rstrip('0').rstrip('.'),
            "metadata": {
                "network": burn.network
            }
        }
        
        # Only add reserves if available
        if reserves is not None:
            burn_data["reserves"] = reserves
        
        return JoinExitEventWithBlock(**burn_data)


# Global serializer service
serializer_service = SerializerService()
