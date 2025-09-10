import os
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration - read from .env
    log_level: str
    max_block_range: int
    
    # Network Configuration - read from .env
    networks: str  # Comma-separated list of networks
    network: Optional[str] = None  # Single network mode when set
    
    # Subgraph URLs - dynamically based on networks
    # These will be read from .env with pattern: {NETWORK}_SUBGRAPH_URL
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def networks_list(self) -> List[str]:
        """Parse networks from comma-separated string"""
        return [network.strip() for network in self.networks.split(",") if network.strip()]
    
    @property
    def active_networks(self) -> List[str]:
        """Get active networks (single network mode or all configured)"""
        all_networks = self.networks_list
        if self.network and self.network in all_networks:
            return [self.network]  # Single network mode
        return all_networks
    
    def get_subgraph_url(self, network: str) -> str:
        """Get subgraph URL for specific network from environment variables"""
        env_var_name = f"{network.upper()}_SUBGRAPH_URL"
        return os.getenv(env_var_name, "")


settings = Settings()
