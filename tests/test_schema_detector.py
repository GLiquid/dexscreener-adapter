import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.schema_detector import SchemaDetector, SubgraphSchemaVersion


class TestSchemaDetector:
    """Test schema detection functionality"""
    
    @pytest.fixture
    def detector(self):
        return SchemaDetector()
    
    @pytest.fixture
    def mock_session(self):
        session = MagicMock(spec=aiohttp.ClientSession)
        return session
    
    @pytest.mark.asyncio
    async def test_introspection_v2_detection(self, detector, mock_session):
        """Test V2 schema detection via introspection"""
        # Mock introspection response with reserves fields
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "__schema": {
                    "types": [
                        {
                            "name": "Swap",
                            "fields": [
                                {"name": "id"},
                                {"name": "amount0"},
                                {"name": "amount1"},
                                {"name": "reserves0"},  # V2 field
                                {"name": "reserves1"}   # V2 field
                            ]
                        }
                    ]
                }
            }
        })
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        result = await detector.detect_schema_version(
            mock_session, 
            "https://test-subgraph.com", 
            "polygon"
        )
        
        assert result == SubgraphSchemaVersion.V2_WITH_RESERVES
    
    @pytest.mark.asyncio
    async def test_introspection_v1_detection(self, detector, mock_session):
        """Test V1 schema detection via introspection"""
        # Mock introspection response without reserves fields
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "__schema": {
                    "types": [
                        {
                            "name": "Swap",
                            "fields": [
                                {"name": "id"},
                                {"name": "amount0"},
                                {"name": "amount1"}
                                # No reserves0/reserves1 fields
                            ]
                        }
                    ]
                }
            }
        })
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        result = await detector.detect_schema_version(
            mock_session, 
            "https://test-subgraph.com", 
            "ethereum"
        )
        
        assert result == SubgraphSchemaVersion.V1_NO_RESERVES
    
    @pytest.mark.asyncio
    async def test_introspection_fallback_to_field_test(self, detector, mock_session):
        """Test fallback to field test when introspection fails"""
        # Mock introspection failure, then successful field test
        responses = [
            # First call (introspection) - fails
            AsyncMock(status=500),
            # Second call (field test) - succeeds with no field errors
            AsyncMock(status=200, json=AsyncMock(return_value={"data": {"swaps": []}}))
        ]
        
        mock_session.post.return_value.__aenter__.side_effect = responses
        
        result = await detector.detect_schema_version(
            mock_session, 
            "https://test-subgraph.com", 
            "arbitrum"
        )
        
        assert result == SubgraphSchemaVersion.V2_WITH_RESERVES  # Field test succeeded
        assert mock_session.post.call_count == 2  # Two calls made
    
    @pytest.mark.asyncio
    async def test_schema_analysis(self, detector, mock_session):
        """Test schema analysis functionality"""
        # Mock full introspection response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "__schema": {
                    "types": [
                        {
                            "name": "Swap",
                            "fields": [
                                {"name": "id"},
                                {"name": "amount0"},
                                {"name": "reserves0"}
                            ]
                        },
                        {
                            "name": "Pool",
                            "fields": [
                                {"name": "id"},
                                {"name": "token0"},
                                {"name": "token1"}
                            ]
                        }
                    ]
                }
            }
        })
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        schema_info = await detector.get_full_schema_info(mock_session, "https://test.com")
        assert schema_info is not None
        
        analysis = detector.analyze_schema_types(schema_info, ["Swap", "Pool"])
        assert "Swap" in analysis
        assert "Pool" in analysis
        assert "reserves0" in analysis["Swap"]
        assert "token0" in analysis["Pool"]
    @pytest.mark.asyncio
    async def test_detect_v2_schema_success(self, detector, mock_session):
        """Test successful V2 schema detection via field test (fallback)"""
        # Mock introspection failure, then successful field test
        responses = [
            # First call (introspection) - returns error
            AsyncMock(status=200, json=AsyncMock(return_value={"errors": ["Introspection disabled"]})),
            # Second call (field test) - succeeds without field errors  
            AsyncMock(status=200, json=AsyncMock(return_value={"data": {"swaps": []}}))
        ]
        
        mock_session.post.return_value.__aenter__.side_effect = responses
        
        result = await detector.detect_schema_version(
            mock_session, 
            "https://test-subgraph.com", 
            "polygon"
        )
        
        assert result == SubgraphSchemaVersion.V2_WITH_RESERVES
        
        # Check cache
        cached = detector.get_cached_schema("polygon", "https://test-subgraph.com")
        assert cached == SubgraphSchemaVersion.V2_WITH_RESERVES
    
    @pytest.mark.asyncio
    async def test_detect_v1_schema_field_error(self, detector, mock_session):
        """Test V1 schema detection via field error (fallback)"""
        # Mock introspection failure, then field test with reserves error
        responses = [
            # First call (introspection) - fails
            AsyncMock(status=500),
            # Second call (field test) - field error about reserves0
            AsyncMock(status=200, json=AsyncMock(return_value={
                "errors": [
                    {
                        "message": "Cannot query field 'reserves0' on type 'Swap'"
                    }
                ]
            }))
        ]
        
        mock_session.post.return_value.__aenter__.side_effect = responses
        
        result = await detector.detect_schema_version(
            mock_session, 
            "https://test-subgraph.com", 
            "ethereum"
        )
        
        assert result == SubgraphSchemaVersion.V1_NO_RESERVES
    
    @pytest.mark.asyncio
    async def test_detect_v1_schema_fallback(self, detector, mock_session):
        """Test V1 schema detection as fallback when request fails"""
        # Mock request failure
        mock_session.post.side_effect = Exception("Connection error")
        
        result = await detector.detect_schema_version(
            mock_session, 
            "https://test-subgraph.com", 
            "arbitrum"
        )
        
        assert result == SubgraphSchemaVersion.V1_NO_RESERVES
    
    def test_manual_schema_override(self, detector):
        """Test manual schema version override"""
        detector.set_manual_schema(
            "base", 
            "https://test-subgraph.com", 
            SubgraphSchemaVersion.V2_WITH_RESERVES
        )
        
        cached = detector.get_cached_schema("base", "https://test-subgraph.com")
        assert cached == SubgraphSchemaVersion.V2_WITH_RESERVES
    
    def test_cache_isolation(self, detector):
        """Test that cache keys are properly isolated"""
        detector.set_manual_schema(
            "network1", 
            "https://url1.com", 
            SubgraphSchemaVersion.V1_NO_RESERVES
        )
        detector.set_manual_schema(
            "network2", 
            "https://url2.com", 
            SubgraphSchemaVersion.V2_WITH_RESERVES
        )
        
        result1 = detector.get_cached_schema("network1", "https://url1.com")
        result2 = detector.get_cached_schema("network2", "https://url2.com")
        result3 = detector.get_cached_schema("network1", "https://url2.com")  # Different URL
        
        assert result1 == SubgraphSchemaVersion.V1_NO_RESERVES
        assert result2 == SubgraphSchemaVersion.V2_WITH_RESERVES
        assert result3 is None  # Different URL, not cached
