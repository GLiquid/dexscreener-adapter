import logging
from typing import List, Union, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from app.models import (
    LatestBlockResponse, AssetResponse, PairResponse, 
    SwapEventWithBlock, JoinExitEventWithBlock
)
from app.services import (
    event_service, serializer_service, subgraph_service
)
from app.utils import is_valid_address, normalize_address
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{network}/latest-block")
async def get_latest_block_for_network(
    network: str = Path(..., description="Network name")
) -> LatestBlockResponse:
    """Get the latest block number for specific network"""
    try:
        if network not in settings.active_networks:
            raise HTTPException(status_code=400, detail=f"Unsupported network: {network}")
        
        # Get latest block from subgraph
        block_info = await subgraph_service.get_latest_block(network)
        if not block_info:
            raise HTTPException(status_code=500, detail=f"Could not fetch latest block from {network}")
        
        block = await serializer_service.serialize_block(network, block_info["blockNumber"])
        return LatestBlockResponse(block=block)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch latest block for {network}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest block")


@router.get("/{network}/asset")
async def get_asset(
    network: str = Path(..., description="Network name"),
    id: str = Query(..., description="Token address")
) -> AssetResponse:
    """Get asset information by token address"""
    try:
        if network not in settings.active_networks:
            raise HTTPException(status_code=400, detail=f"Unsupported network: {network}")
            
        if not is_valid_address(id):
            raise HTTPException(status_code=400, detail="Invalid address format")
        
        address = normalize_address(id)
        asset = await serializer_service.serialize_asset(network, address)
        return AssetResponse(asset=asset)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch asset {id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch asset")


@router.get("/{network}/pair") 
async def get_pair(
    network: str = Path(..., description="Network name"),
    id: str = Query(..., description="Pool address")
) -> PairResponse:
    """Get pair information by pool address"""
    try:
        if network not in settings.active_networks:
            raise HTTPException(status_code=400, detail=f"Unsupported network: {network}")
            
        if not is_valid_address(id):
            raise HTTPException(status_code=400, detail="Invalid address format")
        
        address = normalize_address(id)
        pair = await serializer_service.serialize_pair(network, address)
        return PairResponse(pair=pair)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch pair {id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pair")


@router.get("/{network}/events")
async def get_events(
    network: str = Path(..., description="Network name"),
    fromBlock: int = Query(..., description="Start block number"),
    toBlock: int = Query(..., description="End block number")
) -> dict:
    """Get all events (swaps, mints, burns) in the specified block range"""
    try:
        if network not in settings.active_networks:
            raise HTTPException(status_code=400, detail=f"Unsupported network: {network}")
            
        if fromBlock > toBlock:
            raise HTTPException(status_code=400, detail="fromBlock cannot be greater than toBlock")
        
        if toBlock - fromBlock > settings.max_block_range:
            raise HTTPException(
                status_code=400, 
                detail=f"Block range too large (max {settings.max_block_range} blocks)"
            )
        
        all_events: List[Union[SwapEventWithBlock, JoinExitEventWithBlock]] = []
        
        try:
            # Get all events in one optimized call
            events = await event_service.get_all_events(network, fromBlock, toBlock)
            
            # Process swap events
            for swap in events.get("swaps", []):
                swap_event = await serializer_service.serialize_swap_event(swap)
                all_events.append(swap_event)
            
            # Process mint events (join)
            for mint in events.get("mints", []):
                mint_event = await serializer_service.serialize_mint_event(mint)
                all_events.append(mint_event)
            
            # Process burn events (exit)
            for burn in events.get("burns", []):
                burn_event = await serializer_service.serialize_burn_event(burn)
                all_events.append(burn_event)
                
        except Exception as e:
            logger.error(f"Error fetching events from {network}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch events from {network}")
        
        # Sort all events by block number, then by transaction index, then by event index
        all_events.sort(key=lambda x: (
            x.block.blockNumber, 
            x.txnIndex, 
            x.eventIndex
        ))
        
        return {"events": [event.dict() for event in all_events]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch events: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch events")
