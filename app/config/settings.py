import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuration settings loaded from environment variables"""
    
    def __init__(self):
        # API Configuration
        self.log_level = self._get_required_env("LOG_LEVEL")
        self.max_block_range = int(self._get_required_env("MAX_BLOCK_RANGE"))
        
        # Network Configuration
        self.networks = self._get_required_env("NETWORKS")
        self.network = os.getenv("NETWORK")  
        
        # Schema configuration
        self.subgraph_schemas = os.getenv("SUBGRAPH_SCHEMAS")
    
    def _get_required_env(self, key: str) -> str:
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
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
        url = os.getenv(env_var_name, "")
        if not url:
            raise ValueError(f"Subgraph URL for network '{network}' not found. Please set {env_var_name} in .env file")
        return url
    
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


def validate_settings() -> None:
    """Validate that all required settings are properly configured"""
    try:
        settings = Settings()
        print(f"✅ Settings validation passed!")
        print(f"   Networks: {settings.active_networks}")
        print(f"   Log level: {settings.log_level}")
        print(f"   Max block range: {settings.max_block_range}")
        

        for network in settings.active_networks:
            try:
                url = settings.get_subgraph_url(network)
                print(f"   {network.upper()}_SUBGRAPH_URL: ✅")
            except Exception as e:
                print(f"   {network.upper()}_SUBGRAPH_URL: ❌ {e}")
                
    except Exception as e:
        print(f"❌ Settings validation failed: {e}")
        raise

settings = Settings()
