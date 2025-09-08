import os
from typing import Dict, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    log_level: str = "INFO"
    
    # Infura Configuration
    infura_api_key: str = "your_infura_key_here"
    
    # Redis Configuration  
    redis_url: str = "redis://localhost:6379"
    
    # Network Configuration
    networks: List[str] = ["ethereum", "polygon", "arbitrum", "base"]
    
    # RPC URLs
    ethereum_rpc_url: str = "https://mainnet.infura.io/v3/${INFURA_API_KEY}"
    polygon_rpc_url: str = "https://polygon-mainnet.infura.io/v3/${INFURA_API_KEY}"
    arbitrum_rpc_url: str = "https://arbitrum-mainnet.infura.io/v3/${INFURA_API_KEY}"
    base_rpc_url: str = "https://base-mainnet.infura.io/v3/${INFURA_API_KEY}"
    
    # Factory Addresses - will be populated from network configs
    factory_addresses: Dict[str, Dict[str, str]] = {}
    
    # Cache TTL settings (seconds)
    cache_ttl_blocks: int = 5
    cache_ttl_assets: int = 300
    cache_ttl_pairs: int = 60
    
    class Config:
        env_file = ".env"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize factory addresses after parent init
        self.factory_addresses = {}
        self._setup_factory_addresses()
        self._setup_rpc_urls()
    
    def _setup_factory_addresses(self):
        """Setup factory addresses for different networks and versions"""
        self.factory_addresses = {
            "ethereum": {
                "v1": os.getenv("ETHEREUM_FACTORY_V1", ""),
                "v2": os.getenv("ETHEREUM_FACTORY_V2", ""),
            },
            "polygon": {
                "v1": os.getenv("POLYGON_FACTORY_V1", ""),
                "v2": os.getenv("POLYGON_FACTORY_V2", ""),
            },
            "arbitrum": {
                "v1": os.getenv("ARBITRUM_FACTORY_V1", ""),
                "v2": os.getenv("ARBITRUM_FACTORY_V2", ""),
            },
            "base": {
                "v1": os.getenv("BASE_FACTORY_V1", ""),
                "v2": os.getenv("BASE_FACTORY_V2", ""),
            }
        }
    
    def _setup_rpc_urls(self):
        """Setup RPC URLs with Infura API key injection"""
        if "${INFURA_API_KEY}" in self.ethereum_rpc_url:
            self.ethereum_rpc_url = self.ethereum_rpc_url.replace("${INFURA_API_KEY}", self.infura_api_key)
        if "${INFURA_API_KEY}" in self.polygon_rpc_url:
            self.polygon_rpc_url = self.polygon_rpc_url.replace("${INFURA_API_KEY}", self.infura_api_key)
        if "${INFURA_API_KEY}" in self.arbitrum_rpc_url:
            self.arbitrum_rpc_url = self.arbitrum_rpc_url.replace("${INFURA_API_KEY}", self.infura_api_key)
        if "${INFURA_API_KEY}" in self.base_rpc_url:
            self.base_rpc_url = self.base_rpc_url.replace("${INFURA_API_KEY}", self.infura_api_key)
    
    def get_rpc_url(self, network: str) -> str:
        """Get RPC URL for specific network"""
        rpc_mapping = {
            "ethereum": self.ethereum_rpc_url,
            "polygon": self.polygon_rpc_url,
            "arbitrum": self.arbitrum_rpc_url,
            "base": self.base_rpc_url,
        }
        return rpc_mapping.get(network, "")
    
    def get_factory_address(self, network: str, version: str) -> str:
        """Get factory address for specific network and version"""
        return self.factory_addresses.get(network, {}).get(version, "")


settings = Settings()
