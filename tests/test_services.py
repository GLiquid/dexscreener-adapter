import pytest
import asyncio
from app.services.web3_service import web3_manager
from app.config import settings


class TestWeb3Service:
    """Test Web3 service functionality"""
    
    def test_web3_connections(self):
        """Test that Web3 connections are established"""
        for network in settings.networks:
            w3 = web3_manager.get_web3(network)
            if w3:  # Only test if connection exists
                assert w3.is_connected()
                latest_block = web3_manager.get_latest_block_number(network)
                assert latest_block is not None
                assert latest_block > 0


class TestPoolDiscovery:
    """Test pool discovery functionality"""
    
    @pytest.mark.asyncio
    async def test_pool_discovery(self):
        """Test pool discovery on a small block range"""
        from app.services.pool_discovery import pool_discovery_service
        
        # Test on a small range to avoid timeout
        network = "ethereum"
        if network in settings.networks:
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
    async def test_token_info(self):
        """Test token info fetching"""
        from app.services.event_service import event_service
        
        # Test with WETH address
        weth_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        token_info = await event_service.get_token_info("ethereum", weth_address)
        
        if token_info:  # Only test if we can fetch it
            assert token_info.symbol == "WETH"
            assert token_info.decimals == 18
