import logging
from typing import List, Union, Optional
from fastapi import APIRouter, HTTPException, Query
from app.models import (
    LatestBlockResponse, AssetResponse, PairResponse, 
    SwapEventWithBlock, JoinExitEventWithBlock
)
from app.services import (
    web3_manager, event_service, serializer_service, pool_discovery_service
)
from app.utils import is_valid_address, normalize_address
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def _detect_network_from_address(address: str) -> Optional[str]:
    """
    Detect network from address by checking which network has this pool/token
    In production, you might want to use a more sophisticated approach
    """
    # For now, we'll try each network until we find the address
    for network in settings.networks:
        # Check if it's a known pool
        pool_info = pool_discovery_service.get_pool_info(address)
        if pool_info and pool_info.network == network:
            return network
        
        # Could also check if it's a token by calling contract
        w3 = web3_manager.get_web3(network)
        if w3:
            try:
                # Try to call a simple contract function to see if address exists
                code = w3.eth.get_code(address)
                if code and len(code) > 2:  # Has contract code
                    return network
            except:
                continue
    
    # Default to ethereum if not found
    return "ethereum"


@router.get("/latest-block")
async def get_latest_block() -> LatestBlockResponse:
    """Get the latest block number across all networks"""
    try:
        # Find the highest block number across all networks
        latest_block = 0
        latest_network = ""
        
        for network in settings.networks:
            block_number = web3_manager.get_latest_block_number(network)
            if block_number and block_number > latest_block:
                latest_block = block_number
                latest_network = network
        
        if latest_block == 0:
            raise HTTPException(status_code=500, detail="Could not fetch latest block from any network")
        
        block = serializer_service.serialize_block(latest_network, latest_block)
        return LatestBlockResponse(block=block)
        
    except Exception as e:
        logger.error(f"Failed to fetch latest block: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest block")


@router.get("/asset")
async def get_asset(id: str = Query(..., description="Token address")) -> AssetResponse:
    """Get asset information by token address"""
    try:
        if not is_valid_address(id):
            raise HTTPException(status_code=400, detail="Invalid address format")
        
        address = normalize_address(id)
        network = _detect_network_from_address(address)
        
        if not network:
            raise HTTPException(status_code=404, detail="Asset not found on any supported network")
        
        asset = await serializer_service.serialize_asset(network, address)
        return AssetResponse(asset=asset)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch asset {id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch asset")


@router.get("/pair") 
async def get_pair(id: str = Query(..., description="Pool address")) -> PairResponse:
    """Get pair information by pool address"""
    try:
        if not is_valid_address(id):
            raise HTTPException(status_code=400, detail="Invalid address format")
        
        address = normalize_address(id)
        network = _detect_network_from_address(address)
        
        if not network:
            raise HTTPException(status_code=404, detail="Pair not found on any supported network")
        
        pair = await serializer_service.serialize_pair(network, address)
        return PairResponse(pair=pair)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch pair {id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pair")


@router.get("/events")
async def get_events(
    fromBlock: int = Query(..., description="Start block number"),
    toBlock: int = Query(..., description="End block number"),
    network: Optional[str] = Query(None, description="Network name (optional)")
) -> dict:
    """Get all events (swaps, mints, burns) in the specified block range"""
    try:
        if fromBlock > toBlock:
            raise HTTPException(status_code=400, detail="fromBlock cannot be greater than toBlock")
        
        if toBlock - fromBlock > 10000:  # Limit range to prevent timeout
            raise HTTPException(status_code=400, detail="Block range too large (max 10000 blocks)")
        
        # If network not specified, use all networks
        networks_to_query = [network] if network else settings.networks
        
        all_events: List[Union[SwapEventWithBlock, JoinExitEventWithBlock]] = []
        
        for net in networks_to_query:
            if net not in settings.networks:
                continue
                
            try:
                # Get swap events
                swaps = await event_service.get_swap_events(net, fromBlock, toBlock)
                for swap in swaps:
                    swap_event = await serializer_service.serialize_swap_event(swap)
                    all_events.append(swap_event)
                
                # Get mint events (join)
                mints = await event_service.get_mint_events(net, fromBlock, toBlock)
                for mint in mints:
                    mint_event = await serializer_service.serialize_mint_event(mint)
                    all_events.append(mint_event)
                
                # Get burn events (exit)
                burns = await event_service.get_burn_events(net, fromBlock, toBlock)
                for burn in burns:
                    burn_event = await serializer_service.serialize_burn_event(burn)
                    all_events.append(burn_event)
                    
            except Exception as e:
                logger.error(f"Error fetching events from {net}: {e}")
                continue
        
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
