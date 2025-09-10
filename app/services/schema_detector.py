import logging
from typing import Dict, Optional, List
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class SubgraphSchemaVersion(Enum):
    """Supported subgraph schema versions"""
    V1_NO_RESERVES = "v1"  # Original schema without reserves
    V2_WITH_RESERVES = "v2"  # New schema with reserves0/reserves1 fields


class SchemaDetector:
    """Service for detecting subgraph schema capabilities"""
    
    def __init__(self):
        self._schema_cache: Dict[str, SubgraphSchemaVersion] = {}
    
    async def detect_schema_version(self, session: aiohttp.ClientSession, subgraph_url: str, network: str) -> SubgraphSchemaVersion:
        """
        Detect subgraph schema version using GraphQL introspection
        Returns cached result if already detected
        """
        cache_key = f"{network}:{subgraph_url}"
        
        if cache_key in self._schema_cache:
            return self._schema_cache[cache_key]
        
        # Try introspection query first (more reliable)
        version = await self._detect_via_introspection(session, subgraph_url, network)
        if version:
            self._schema_cache[cache_key] = version
            return version
        
        # Fallback to field test if introspection fails
        version = await self._detect_via_field_test(session, subgraph_url, network)
        self._schema_cache[cache_key] = version
        return version
    
    async def _detect_via_introspection(self, session: aiohttp.ClientSession, subgraph_url: str, network: str) -> Optional[SubgraphSchemaVersion]:
        """Detect schema using GraphQL introspection query"""
        introspection_query = """
        query IntrospectionQuery {
            __schema {
                types {
                    name
                    fields {
                        name
                    }
                }
            }
        }
        """
        
        try:
            payload = {"query": introspection_query}
            async with session.post(subgraph_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "errors" in data:
                        logger.warning(f"Introspection query failed for {network}: {data['errors']}")
                        return None
                    
                    # Look for Swap type and check if it has reserves0/reserves1 fields
                    schema_data = data.get("data", {}).get("__schema", {})
                    types = schema_data.get("types", [])
                    
                    swap_type = None
                    for type_def in types:
                        if type_def.get("name") == "Swap":
                            swap_type = type_def
                            break
                    
                    if not swap_type:
                        logger.warning(f"Swap type not found in schema for {network}")
                        return None
                    
                    # Check if reserves fields exist
                    field_names = [field.get("name") for field in swap_type.get("fields", [])]
                    has_reserves0 = "reserves0" in field_names
                    has_reserves1 = "reserves1" in field_names
                    
                    if has_reserves0 and has_reserves1:
                        logger.info(f"Schema V2 detected via introspection for {network}: reserves fields found")
                        return SubgraphSchemaVersion.V2_WITH_RESERVES
                    else:
                        logger.info(f"Schema V1 detected via introspection for {network}: no reserves fields")
                        return SubgraphSchemaVersion.V1_NO_RESERVES
                        
        except Exception as e:
            logger.warning(f"Introspection failed for {network}: {e}")
            return None
        
        return None
    
    async def _detect_via_field_test(self, session: aiohttp.ClientSession, subgraph_url: str, network: str) -> SubgraphSchemaVersion:
        """Fallback: detect schema by testing field availability"""
        detection_query = """
        query DetectSchema {
            swaps(first: 1) {
                id
                amount0
                amount1
                reserves0
                reserves1
            }
        }
        """
        
        try:
            payload = {"query": detection_query}
            async with session.post(subgraph_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if query succeeded without errors about unknown fields
                    if "errors" in data:
                        # Look for field-related errors
                        errors = data["errors"]
                        for error in errors:
                            error_message = error.get("message", "").lower()
                            if any(keyword in error_message for keyword in ["reserves0", "reserves1", "field", "unknown"]):
                                logger.info(f"Schema V1 detected via field test for {network}: no reserves fields")
                                return SubgraphSchemaVersion.V1_NO_RESERVES
                    
                    # If no field errors, assume V2 schema
                    logger.info(f"Schema V2 detected via field test for {network}: reserves fields available")
                    return SubgraphSchemaVersion.V2_WITH_RESERVES
                    
        except Exception as e:
            logger.warning(f"Field test failed for {network}, defaulting to V1: {e}")
        
        # Default to V1 if both methods fail
        logger.info(f"Schema detection failed for {network}, defaulting to V1")
        return SubgraphSchemaVersion.V1_NO_RESERVES
    
    def get_cached_schema(self, network: str, subgraph_url: str) -> Optional[SubgraphSchemaVersion]:
        """Get cached schema version if available"""
        cache_key = f"{network}:{subgraph_url}"
        return self._schema_cache.get(cache_key)
    
    def set_manual_schema(self, network: str, subgraph_url: str, version: SubgraphSchemaVersion):
        """Manually set schema version (for config override)"""
        cache_key = f"{network}:{subgraph_url}"
        self._schema_cache[cache_key] = version
        logger.info(f"Manual schema override for {network}: {version.value}")
    
    async def get_full_schema_info(self, session: aiohttp.ClientSession, subgraph_url: str) -> Optional[Dict]:
        """Get complete schema information for debugging/analysis"""
        full_introspection_query = """
        query FullIntrospectionQuery {
            __schema {
                types {
                    name
                    kind
                    description
                    fields {
                        name
                        type {
                            name
                            kind
                            ofType {
                                name
                                kind
                            }
                        }
                        description
                    }
                }
            }
        }
        """
        
        try:
            payload = {"query": full_introspection_query}
            async with session.post(subgraph_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if "errors" not in data:
                        return data.get("data", {}).get("__schema", {})
                    else:
                        logger.error(f"Full introspection failed: {data['errors']}")
        except Exception as e:
            logger.error(f"Full introspection query failed: {e}")
        
        return None
    
    def analyze_schema_types(self, schema_info: Dict, type_names: List[str] = None) -> Dict[str, List[str]]:
        """Analyze schema and return field information for specific types"""
        if type_names is None:
            type_names = ["Swap", "Mint", "Burn", "Pool"]
        
        result = {}
        types = schema_info.get("types", [])
        
        for type_def in types:
            type_name = type_def.get("name")
            if type_name in type_names:
                fields = type_def.get("fields", [])
                field_names = [field.get("name") for field in fields if field.get("name")]
                result[type_name] = sorted(field_names)
        
        return result


# Global schema detector instance
schema_detector = SchemaDetector()
