import pytest
from unittest.mock import AsyncMock, patch
from app.services.serializer_service import SerializerService
from app.models.algebra import AlgebraSwap, AlgebraMint, AlgebraBurn
from app.models.dex_screener import Reserves


class TestReservesSerialization:
    """Test reserves serialization in DEX Screener format"""
    
    @pytest.fixture
    def serializer(self):
        return SerializerService()
    
    @pytest.fixture
    def mock_pool_info(self):
        """Mock pool info for serialization"""
        pool_info = AsyncMock()
        pool_info.address = "0xpool123"
        pool_info.token0 = "0xtoken0"
        pool_info.token1 = "0xtoken1"
        return pool_info
    
    @pytest.fixture
    def mock_tokens(self):
        """Mock token info for serialization"""
        token0 = AsyncMock()
        token0.address = "0xtoken0"
        token0.decimals = 18
        token0.symbol = "TOKEN0"
        
        token1 = AsyncMock()
        token1.address = "0xtoken1"  
        token1.decimals = 6
        token1.symbol = "TOKEN1"
        
        return token0, token1
    
    @pytest.mark.asyncio
    @patch('app.services.serializer_service.pool_discovery_service')
    @patch('app.services.serializer_service.event_service')
    async def test_swap_serialization_with_reserves(self, mock_event_service, mock_pool_discovery, serializer, mock_pool_info, mock_tokens):
        """Test swap event serialization with reserves"""
        token0, token1 = mock_tokens
        
        # Setup mocks
        mock_pool_discovery.get_pool_info.return_value = mock_pool_info
        mock_event_service.get_token_info.side_effect = [token0, token1]
        
        # Create swap with reserves
        swap = AlgebraSwap(
            tx_hash="0x123abc",
            tx_index=1,
            log_index=5,
            block_number=18000000,
            block_timestamp=1640995200,
            pool_address="0xpool123",
            sender="0xsender",
            recipient="0xrecipient", 
            tx_origin="0xorigin",
            amount0=1000000000000000000,  # 1.0 token0 (18 decimals)
            amount1=-2000000,  # -2.0 token1 (6 decimals)
            sqrt_price_x96=1000000000000000000,
            liquidity=500000,
            tick=100,
            network="polygon",
            reserves0=123.456789,  # Decimal format reserves
            reserves1=987.654321
        )
        
        # Mock price calculation
        with patch('app.services.serializer_service.calculate_price_from_sqrt_price', return_value="2.0"):
            result = await serializer.serialize_swap_event(swap)
        
        # Verify reserves are properly formatted
        assert result.reserves is not None
        assert isinstance(result.reserves, Reserves)
        assert result.reserves.asset0 == "123.456789"
        assert result.reserves.asset1 == "987.654321"
        
        # Verify other fields
        assert result.txnId == "0x123abc"
        assert result.maker == "0xorigin"
        assert result.pairId == "0xpool123"
    
    @pytest.mark.asyncio
    @patch('app.services.serializer_service.pool_discovery_service')
    @patch('app.services.serializer_service.event_service')
    async def test_swap_serialization_without_reserves(self, mock_event_service, mock_pool_discovery, serializer, mock_pool_info, mock_tokens):
        """Test swap event serialization without reserves (backward compatibility)"""
        token0, token1 = mock_tokens
        
        # Setup mocks
        mock_pool_discovery.get_pool_info.return_value = mock_pool_info
        mock_event_service.get_token_info.side_effect = [token0, token1]
        
        # Create swap without reserves
        swap = AlgebraSwap(
            tx_hash="0x123abc",
            tx_index=1,
            log_index=5,
            block_number=18000000,
            block_timestamp=1640995200,
            pool_address="0xpool123",
            sender="0xsender",
            recipient="0xrecipient",
            tx_origin="0xorigin",
            amount0=1000000000000000000,
            amount1=-2000000,
            sqrt_price_x96=1000000000000000000,
            liquidity=500000,
            tick=100,
            network="polygon"
            # No reserves provided
        )
        
        # Mock price calculation
        with patch('app.services.serializer_service.calculate_price_from_sqrt_price', return_value="2.0"):
            result = await serializer.serialize_swap_event(swap)
        
        # Verify reserves are None (backward compatibility)
        assert result.reserves is None
        
        # Verify other fields still work
        assert result.txnId == "0x123abc"
        assert result.maker == "0xorigin"
    
    @pytest.mark.asyncio 
    @patch('app.services.serializer_service.pool_discovery_service')
    @patch('app.services.serializer_service.event_service')
    async def test_mint_serialization_with_reserves(self, mock_event_service, mock_pool_discovery, serializer, mock_pool_info, mock_tokens):
        """Test mint event serialization with reserves"""
        token0, token1 = mock_tokens
        
        # Setup mocks
        mock_pool_discovery.get_pool_info.return_value = mock_pool_info
        mock_event_service.get_token_info.side_effect = [token0, token1]
        
        # Create mint with reserves
        mint = AlgebraMint(
            tx_hash="0x456def",
            tx_index=2,
            log_index=10,
            block_number=18000001,
            block_timestamp=1640995260,
            pool_address="0xpool123",
            owner="0xowner",
            sender="0xsender",
            tx_origin="0xorigin",
            amount0=500000000000000000,
            amount1=1000000,
            tick_lower=-100,
            tick_upper=100,
            amount=1000000,
            network="ethereum",
            reserves0=0.0001,  # Very small reserves
            reserves1=999999.123456  # Large reserves
        )
        
        result = await serializer.serialize_mint_event(mint)
        
        # Verify reserves formatting
        assert result.reserves is not None
        assert result.reserves.asset0 == "0.0001"
        assert result.reserves.asset1 == "999999.123456"
        
        # Verify event type
        assert result.eventType == "join"
