import os
from typing import Dict, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Configuration - must be provided via .env
    log_level: str
    max_block_range: int
    
    # Network Configuration - must be provided via .env
    networks: str
    network: Optional[str] = None
    
    # Schema configuration - optional manual override
    # Format: network1:v1,network2:v2 where v1/v2 are schema versions
    subgraph_schemas: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
        env_prefix="",  # No prefix for env vars
    )
    
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
    
    def get_subgraph_schema_version(self, network: str) -> Optional[str]:
        """Get manually configured schema version for network, if any"""
        if not self.subgraph_schemas:
            return None
        
        schema_mappings = {}
        for mapping in self.subgraph_schemas.split(","):
            if ":" in mapping:
                net, version = mapping.strip().split(":", 1)
                schema_mappings[net.strip()] = version.strip()
        
        return schema_mappings.get(network)


settings = Settings()
