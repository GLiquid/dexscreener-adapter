import pytest
from app.models.algebra import AlgebraSwap, AlgebraMint, AlgebraBurn


class TestAlgebraModels:
    """Test Algebra models with reserves support"""
    
    def test_swap_with_reserves(self):
        """Test AlgebraSwap with reserves fields"""
        swap = AlgebraSwap(
            tx_hash="0x123",
            tx_index=0,
            log_index=1,
            block_number=12345,
            block_timestamp=1640995200,
            pool_address="0xpool",
            sender="0xsender",
            recipient="0xrecipient",
            tx_origin="0xorigin",
            amount0=1000,
            amount1=-2000,
            sqrt_price_x96=12345678901234567890,
            liquidity=1000000,
            tick=200,
            network="polygon",
            reserves0=123.456789,  # Decimal format
            reserves1=987.654321   # Decimal format
        )
        
        assert swap.reserves0 == 123.456789
        assert swap.reserves1 == 987.654321
        assert isinstance(swap.reserves0, float)
        assert isinstance(swap.reserves1, float)
    
    def test_swap_without_reserves(self):
        """Test AlgebraSwap without reserves (backward compatibility)"""
        swap = AlgebraSwap(
            tx_hash="0x123",
            tx_index=0,
            log_index=1,
            block_number=12345,
            block_timestamp=1640995200,
            pool_address="0xpool",
            sender="0xsender",
            recipient="0xrecipient",
            tx_origin="0xorigin",
            amount0=1000,
            amount1=-2000,
            sqrt_price_x96=12345678901234567890,
            liquidity=1000000,
            tick=200,
            network="polygon"
            # reserves0 and reserves1 not provided
        )
        
        assert swap.reserves0 is None
        assert swap.reserves1 is None
    
    def test_mint_with_reserves(self):
        """Test AlgebraMint with reserves fields"""
        mint = AlgebraMint(
            tx_hash="0x123",
            tx_index=0,
            log_index=1,
            block_number=12345,
            block_timestamp=1640995200,
            pool_address="0xpool",
            owner="0xowner",
            sender="0xsender",
            tx_origin="0xorigin",
            amount0=1000,
            amount1=2000,
            tick_lower=-200,
            tick_upper=200,
            amount=5000,
            network="ethereum",
            reserves0=0.0001,  # Small decimal
            reserves1=999999.999999  # Large decimal
        )
        
        assert mint.reserves0 == 0.0001
        assert mint.reserves1 == 999999.999999
    
    def test_burn_with_reserves(self):
        """Test AlgebraBurn with reserves fields"""
        burn = AlgebraBurn(
            tx_hash="0x123",
            tx_index=0,
            log_index=1,
            block_number=12345,
            block_timestamp=1640995200,
            pool_address="0xpool",
            owner="0xowner",
            tx_origin="0xorigin",
            amount0=1000,
            amount1=2000,
            tick_lower=-200,
            tick_upper=200,
            amount=5000,
            network="arbitrum",
            reserves0=42.123456789,
            reserves1=1.000000001
        )
        
        assert burn.reserves0 == 42.123456789
        assert burn.reserves1 == 1.000000001
