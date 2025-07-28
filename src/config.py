"""
Configuration module for Binance Futures Order Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the trading bot"""
    
    # Binance API Configuration
    API_KEY = os.getenv('BINANCE_API_KEY', '')
    API_SECRET = os.getenv('BINANCE_API_SECRET', '')
    
    # Binance Futures Testnet URLs
    TESTNET_BASE_URL = 'https://testnet.binancefuture.com'
    TESTNET_API_URL = 'https://testnet.binancefuture.com/fapi/v1'
    
    # Production URLs (use with caution)
    PRODUCTION_BASE_URL = 'https://fapi.binance.com'
    PRODUCTION_API_URL = 'https://fapi.binance.com/fapi/v1'
    
    # Default settings
    USE_TESTNET = True  # Set to False for production trading
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'bot.log'
    
    # Trading parameters
    DEFAULT_LEVERAGE = 1
    MIN_QUANTITY = 0.001
    MAX_QUANTITY = 1000
    
    # Risk management
    MAX_POSITION_SIZE = 100  # Maximum position size in USDT
    STOP_LOSS_PERCENTAGE = 0.05  # 5% stop loss
    TAKE_PROFIT_PERCENTAGE = 0.10  # 10% take profit
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        if not cls.API_KEY or not cls.API_SECRET:
            raise ValueError("API_KEY and API_SECRET must be set in environment variables")
        return True
    
    @classmethod
    def get_base_url(cls):
        """Get the appropriate base URL based on environment"""
        return cls.TESTNET_BASE_URL if cls.USE_TESTNET else cls.PRODUCTION_BASE_URL
    
    @classmethod
    def get_api_url(cls):
        """Get the appropriate API URL based on environment"""
        return cls.TESTNET_API_URL if cls.USE_TESTNET else cls.PRODUCTION_API_URL
