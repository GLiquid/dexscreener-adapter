import logging
from typing import List, Optional, Dict, Tuple
from app.services.subgraph_service import subgraph_service
from app.models import Token

logger = logging.getLogger(__name__)


class EventService:
    """Service for fetching and processing Algebra events from subgraph"""
    
    def __init__(self):
        self._token_cache: Dict[str, Token] = {}  # address -> token info
    
    async def get_all_events(self, network: str, from_block: int, 
                           to_block: int) -> Dict[str, List]:
        """Get all events (swaps, mints, burns) from Algebra pools in block range via subgraph"""
        
        try:
            events = await subgraph_service.get_all_events(network, from_block, to_block)
            
            # Sort all events by block number and log index
            for event_type in events:
                events[event_type].sort(key=lambda x: (x.block_number, x.log_index))
            
            total_events = sum(len(events[event_type]) for event_type in events)
            logger.info(f"Fetched {total_events} total events from {network} subgraph")
            return events
            
        except Exception as e:
            logger.error(f"Error fetching events from subgraph: {e}")
            return {"swaps": [], "mints": [], "burns": []}
    
    async def get_token_info(self, network: str, token_address: str) -> Optional[Token]:
        """Get token information from subgraph"""
        
        cache_key = f"{network}:{token_address}"
        if cache_key in self._token_cache:
            return self._token_cache[cache_key]
        
        try:
            token = await subgraph_service.get_token(network, token_address)
            
            if token:
                self._token_cache[cache_key] = token
                logger.info(f"Fetched token info for {token_address} from {network} subgraph")
                return token
            else:
                logger.warning(f"Token {token_address} not found in {network} subgraph")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching token info from subgraph: {e}")
            return None


# Global event service
event_service = EventService()
