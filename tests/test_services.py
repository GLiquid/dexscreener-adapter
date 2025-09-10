import pytest
import asyncio
from app.services.subgraph_service import subgraph_service
from app.config import settings


class TestSubgraphService:
    """Test subgraph service functionality"""
    
    @pytest.mark.asyncio
    async def test_subgraph_connections(self):
        """Test that subgraph connections work"""
        for network in settings.active_networks:
            if network in settings.networks_list:
                latest_block = await subgraph_service.get_latest_block(network)
                assert latest_block is not None
                assert latest_block > 0


class TestPoolDiscovery:
    """Test pool discovery functionality"""
    
    @pytest.mark.asyncio
    async def test_pool_discovery(self):
        """Test pool discovery from subgraph"""
        from app.services.pool_discovery import pool_discovery_service
        
        # Test pool discovery from subgraph
        network = "ethereum"
        if network in settings.subgraph_urls:
            pools = await pool_discovery_service.discover_pools(
                network, 
                from_block=18000000,  # Recent block
                to_block=18000100     # Small range
            )
            # Should return a list (might be empty)
            assert isinstance(pools, list)


class TestEventService:
    """Test event service functionality"""
    
    @pytest.mark.asyncio
    async def test_get_swap_events(self):
        """Test swap events from subgraph"""
        from app.services.event_service import event_service
        
        # Test swap events from subgraph
        network = "ethereum"
        if network in settings.subgraph_urls:
            events = await event_service.get_swap_events(
                network,
                from_block=18000000,
                to_block=18000100
            )
            assert isinstance(events, list)
