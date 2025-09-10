import logging
from typing import List, Optional, Dict, Tuple
from app.services.subgraph_service import subgraph_service
from app.models import AlgebraSwap, AlgebraMint, AlgebraBurn, Token
from app.utils import normalize_address

logger = logging.getLogger(__name__)


class EventService:
    """Service for fetching and processing Algebra events from subgraph"""
    
    def __init__(self):
        self._token_cache: Dict[str, Token] = {}  # address -> token info
    
    async def get_swap_events(self, network: str, from_block: int, 
                            to_block: int) -> List[AlgebraSwap]:
        """Get all swap events from Algebra pools in block range via subgraph"""
        
        try:
            swaps = await subgraph_service.get_swaps(network, from_block, to_block)
            
            # Sort by block number and log index
            swaps.sort(key=lambda x: (x.block_number, x.log_index))
            
            logger.info(f"Fetched {len(swaps)} swap events from {network} subgraph")
            return swaps
            
        except Exception as e:
            logger.error(f"Error fetching swap events from subgraph: {e}")
            return []
    
    async def get_mint_events(self, network: str, from_block: int, 
                            to_block: int) -> List[AlgebraMint]:
        """Get all mint events (add liquidity) from Algebra pools via subgraph"""
        
        try:
            mints = await subgraph_service.get_mints(network, from_block, to_block)
            
            # Sort by block number and log index
            mints.sort(key=lambda x: (x.block_number, x.log_index))
            
            logger.info(f"Fetched {len(mints)} mint events from {network} subgraph")
            return mints
            
        except Exception as e:
            logger.error(f"Error fetching mint events from subgraph: {e}")
            return []
    
    async def get_burn_events(self, network: str, from_block: int, 
                            to_block: int) -> List[AlgebraBurn]:
        """Get all burn events (remove liquidity) from Algebra pools via subgraph"""
        
        try:
            burns = await subgraph_service.get_burns(network, from_block, to_block)
            
            # Sort by block number and log index
            burns.sort(key=lambda x: (x.block_number, x.log_index))
            
            logger.info(f"Fetched {len(burns)} burn events from {network} subgraph")
            return burns
            
        except Exception as e:
            logger.error(f"Error fetching burn events from subgraph: {e}")
            return []
    
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
