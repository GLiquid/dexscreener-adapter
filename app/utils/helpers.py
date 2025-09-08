from decimal import Decimal
from typing import Union


def format_amount(amount: Union[int, str], decimals: int) -> str:
    """
    Format token amount from wei to human readable format
    """
    if isinstance(amount, str):
        amount = int(amount)
    
    # Convert to Decimal for precise arithmetic
    decimal_amount = Decimal(amount) / Decimal(10 ** decimals)
    
    # Return as string to preserve precision
    return str(decimal_amount)


def wei_to_readable(amount: Union[int, str], decimals: int = 18) -> str:
    """
    Convert wei amount to readable format
    """
    return format_amount(amount, decimals)


def calculate_price_from_sqrt_price(sqrt_price_x96: int, decimals0: int, decimals1: int) -> str:
    """
    Calculate price from sqrtPriceX96 (Uniswap V3 / Algebra style)
    Price = (sqrtPriceX96 / 2^96)^2 * (10^decimals0 / 10^decimals1)
    """
    sqrt_price = Decimal(sqrt_price_x96) / Decimal(2 ** 96)
    price = sqrt_price ** 2
    
    # Adjust for token decimals
    price = price * (Decimal(10 ** decimals0) / Decimal(10 ** decimals1))
    
    return str(price)


def tick_to_price(tick: int, decimals0: int, decimals1: int) -> str:
    """
    Convert tick to price
    Price = 1.0001^tick * (10^decimals0 / 10^decimals1)
    """
    price = Decimal("1.0001") ** tick
    price = price * (Decimal(10 ** decimals0) / Decimal(10 ** decimals1))
    
    return str(price)


def normalize_address(address: str) -> str:
    """
    Normalize Ethereum address to checksum format
    """
    from web3 import Web3
    return Web3.to_checksum_address(address.lower())


def is_valid_address(address: str) -> bool:
    """
    Check if address is valid Ethereum address
    """
    from web3 import Web3
    try:
        Web3.to_checksum_address(address)
        return True
    except:
        return False
