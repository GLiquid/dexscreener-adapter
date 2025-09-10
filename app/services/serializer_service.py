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
        
        total_supply_formatted = None
        if token.total_supply:
            total_supply_formatted = format_amount(token.total_supply, token.decimals)
        
        return Asset(
            id=token.address,
            name=token.name,
            symbol=token.symbol,
            totalSupply=total_supply_formatted,
            metadata={
                "network": network,
                "decimals": str(token.decimals)
            }
        )
    
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
        
        return Pair(
            id=pool_info.address,
            dexKey=f"{self.dex_key}-{network}",
            asset0Id=token0.address,
            asset1Id=token1.address,
            createdAtBlockNumber=pool_info.created_at_block,
            createdAtBlockTimestamp=pool_info.created_at_timestamp,
            createdAtTxnId=pool_info.created_at_tx,
            creator=pool_info.creator,
            feeBps=fee_bps,
            metadata={
                "network": network,
                "tickSpacing": str(pool_info.tick_spacing),
                "token0Symbol": token0.symbol,
                "token1Symbol": token1.symbol,
                "token0Decimals": str(token0.decimals),
                "token1Decimals": str(token1.decimals)
            }
        )
    
    async def serialize_swap_event(self, swap: AlgebraSwap) -> SwapEventWithBlock:
        """Convert Algebra swap to DEX Screener swap event"""
        
        # Now we have all token info directly from the swap event
        token0 = swap.token0
        token1 = swap.token1
        
        # Get block timestamp from swap data (subgraph includes timestamp)
        block_timestamp = swap.timestamp
        
        # Format amounts
        amount0_formatted = format_amount(abs(swap.amount0), token0.decimals)
        amount1_formatted = format_amount(abs(swap.amount1), token1.decimals)
        
        # Determine direction (which token is in vs out)
        asset0_in = amount0_formatted if swap.amount0 > 0 else None
        asset0_out = amount0_formatted if swap.amount0 < 0 else None
        asset1_in = amount1_formatted if swap.amount1 > 0 else None
        asset1_out = amount1_formatted if swap.amount1 < 0 else None
        
        # Calculate price (price of token0 in terms of token1)
        price_native = calculate_price_from_sqrt_price(
            swap.sqrt_price_x96, token0.decimals, token1.decimals
        )
        
        # Include reserves if available from subgraph
        reserves = None
        if swap.reserves0 is not None and swap.reserves1 is not None:
            # Reserves come in decimal format from subgraph (e.g., 0.0001)
            # Convert to string for DEX Screener API
            reserves = Reserves(
                asset0=str(swap.reserves0),
                asset1=str(swap.reserves1)
            )
        
        return SwapEventWithBlock(
            block=Block(
                blockNumber=swap.block_number,
                blockTimestamp=block_timestamp
            ),
            eventType="swap",
            txnId=swap.tx_hash,
            txnIndex=swap.tx_index,
            eventIndex=swap.log_index,
            maker=swap.tx_origin,  # Use transaction origin instead of sender
            pairId=swap.pool_address,
            asset0In=asset0_in,
            asset1In=asset1_in,
            asset0Out=asset0_out,
            asset1Out=asset1_out,
            priceNative=price_native,
            reserves=reserves,
            metadata={
                "network": swap.network
            }
        )
    
    async def serialize_mint_event(self, mint: AlgebraMint) -> JoinExitEventWithBlock:
        """Convert Algebra mint to DEX Screener join event"""
        
        # Now we have all token info directly from the mint event
        token0 = mint.token0
        token1 = mint.token1
        
        # Get block timestamp from mint data (subgraph includes timestamp)
        block_timestamp = mint.timestamp
        
        amount0_formatted = format_amount(mint.amount0, token0.decimals)
        amount1_formatted = format_amount(mint.amount1, token1.decimals)
        
        # Include reserves if available from subgraph
        reserves = None
        if mint.reserves0 is not None and mint.reserves1 is not None:
            # Reserves come in decimal format from subgraph (e.g., 0.0001)
            # Convert to string for DEX Screener API
            reserves = Reserves(
                asset0=str(mint.reserves0),
                asset1=str(mint.reserves1)
            )
        
        return JoinExitEventWithBlock(
            block=Block(
                blockNumber=mint.block_number,
                blockTimestamp=block_timestamp
            ),
            eventType="join",
            txnId=mint.tx_hash,
            txnIndex=mint.tx_index,
            eventIndex=mint.log_index,
            maker=mint.tx_origin,
            pairId=mint.pool_address,
            amount0=amount0_formatted,
            amount1=amount1_formatted,
            reserves=reserves,
            metadata={
                "network": mint.network
            }
        )
    
    async def serialize_burn_event(self, burn: AlgebraBurn) -> JoinExitEventWithBlock:
        """Convert Algebra burn to DEX Screener exit event"""
        
        # Now we have all token info directly from the burn event
        token0 = burn.token0
        token1 = burn.token1
        
        # Get block timestamp from burn data (subgraph includes timestamp)
        block_timestamp = burn.timestamp
        
        amount0_formatted = format_amount(burn.amount0, token0.decimals)
        amount1_formatted = format_amount(burn.amount1, token1.decimals)
        
        # Include reserves if available from subgraph
        reserves = None
        if burn.reserves0 is not None and burn.reserves1 is not None:
            # Reserves come in decimal format from subgraph (e.g., 0.0001)
            # Convert to string for DEX Screener API
            reserves = Reserves(
                asset0=str(burn.reserves0),
                asset1=str(burn.reserves1)
            )
        
        return JoinExitEventWithBlock(
            block=Block(
                blockNumber=burn.block_number,
                blockTimestamp=block_timestamp
            ),
            eventType="exit",
            txnId=burn.tx_hash,
            txnIndex=burn.tx_index,
            eventIndex=burn.log_index,
            maker=burn.tx_origin,  # Use transaction origin
            pairId=burn.pool_address,
            amount0=amount0_formatted,
            amount1=amount1_formatted,
            reserves=reserves,
            metadata={
                "network": burn.network
            }
        )


# Global serializer service
serializer_service = SerializerService()
