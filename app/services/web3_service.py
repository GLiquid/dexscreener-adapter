import asyncio
import logging
from typing import Dict, Optional, List
from web3 import Web3
from web3.middleware import geth_poa_middleware
from app.config import settings
from app.utils import CHAIN_IDS

logger = logging.getLogger(__name__)


class Web3Manager:
    """Manages Web3 connections for different networks"""
    
    def __init__(self):
        self._connections: Dict[str, Web3] = {}
        self._setup_connections()
    
    def _setup_connections(self):
        """Initialize Web3 connections for all configured networks"""
        for network in settings.networks:
            rpc_url = settings.get_rpc_url(network)
            if rpc_url:
                try:
                    w3 = Web3(Web3.HTTPProvider(rpc_url))
                    
                    # Add PoA middleware for networks that need it
                    if network in ["polygon", "base"]:
                        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    
                    # Test connection
                    if w3.is_connected():
                        self._connections[network] = w3
                        logger.info(f"Connected to {network} network")
                    else:
                        logger.error(f"Failed to connect to {network} network")
                        
                except Exception as e:
                    logger.error(f"Error connecting to {network}: {e}")
    
    def get_web3(self, network: str) -> Optional[Web3]:
        """Get Web3 instance for specific network"""
        return self._connections.get(network)
    
    def get_latest_block_number(self, network: str) -> Optional[int]:
        """Get latest block number for network"""
        w3 = self.get_web3(network)
        if w3:
            try:
                return w3.eth.block_number
            except Exception as e:
                logger.error(f"Error getting latest block for {network}: {e}")
        return None
    
    def get_block(self, network: str, block_number: int) -> Optional[dict]:
        """Get block data"""
        w3 = self.get_web3(network)
        if w3:
            try:
                return w3.eth.get_block(block_number)
            except Exception as e:
                logger.error(f"Error getting block {block_number} for {network}: {e}")
        return None
    
    def get_transaction_receipt(self, network: str, tx_hash: str) -> Optional[dict]:
        """Get transaction receipt"""
        w3 = self.get_web3(network)
        if w3:
            try:
                return w3.eth.get_transaction_receipt(tx_hash)
            except Exception as e:
                logger.error(f"Error getting tx receipt {tx_hash} for {network}: {e}")
        return None
    
    def get_logs(self, network: str, filter_params: dict) -> List[dict]:
        """Get logs with filter"""
        w3 = self.get_web3(network)
        if w3:
            try:
                return w3.eth.get_logs(filter_params)
            except Exception as e:
                logger.error(f"Error getting logs for {network}: {e}")
        return []
    
    def call_contract_function(self, network: str, contract_address: str, 
                             abi: list, function_name: str, *args) -> any:
        """Call contract function"""
        w3 = self.get_web3(network)
        if w3:
            try:
                contract = w3.eth.contract(address=contract_address, abi=abi)
                function = getattr(contract.functions, function_name)
                return function(*args).call()
            except Exception as e:
                logger.error(f"Error calling {function_name} on {contract_address}: {e}")
        return None


# Global Web3 manager instance
web3_manager = Web3Manager()
