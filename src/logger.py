"""
Logging utility for Binance Futures Order Bot
"""
import logging
import os
from datetime import datetime
from typing import Optional
import json

class BotLogger:
    """Custom logger for the trading bot with structured logging"""
    
    def __init__(self, log_file: str = "bot.log", log_level: str = "INFO"):
        self.log_file = log_file
        self.logger = logging.getLogger("BinanceFuturesBot")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_order_attempt(self, order_type: str, symbol: str, side: str, 
                         quantity: float, price: Optional[float] = None, **kwargs):
        """Log order placement attempt"""
        order_data = {
            "action": "ORDER_ATTEMPT",
            "order_type": order_type,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.logger.info(f"Order Attempt: {json.dumps(order_data, indent=2)}")
    
    def log_order_success(self, order_response: dict):
        """Log successful order placement"""
        success_data = {
            "action": "ORDER_SUCCESS",
            "order_id": order_response.get('orderId'),
            "symbol": order_response.get('symbol'),
            "side": order_response.get('side'),
            "quantity": order_response.get('origQty'),
            "price": order_response.get('price'),
            "status": order_response.get('status'),
            "timestamp": datetime.now().isoformat()
        }
        self.logger.info(f"Order Success: {json.dumps(success_data, indent=2)}")
    
    def log_order_error(self, error: Exception, order_details: dict):
        """Log order placement error"""
        error_data = {
            "action": "ORDER_ERROR",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "order_details": order_details,
            "timestamp": datetime.now().isoformat()
        }
        self.logger.error(f"Order Error: {json.dumps(error_data, indent=2)}")
    
    def log_validation_error(self, field: str, value: any, reason: str):
        """Log validation errors"""
        validation_data = {
            "action": "VALIDATION_ERROR",
            "field": field,
            "value": str(value),
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        self.logger.warning(f"Validation Error: {json.dumps(validation_data, indent=2)}")
    
    def log_api_call(self, endpoint: str, method: str, params: dict, response_status: int):
        """Log API calls"""
        api_data = {
            "action": "API_CALL",
            "endpoint": endpoint,
            "method": method,
            "params": params,
            "response_status": response_status,
            "timestamp": datetime.now().isoformat()
        }
        self.logger.debug(f"API Call: {json.dumps(api_data, indent=2)}")
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)

# Global logger instance
bot_logger = BotLogger()
