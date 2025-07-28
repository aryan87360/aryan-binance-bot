"""
Input validation module for Binance Futures Order Bot
"""
import re
from typing import Union, Optional
from decimal import Decimal, InvalidOperation
from src.logger import bot_logger
from src.config import Config

class OrderValidator:
    """Validates trading order inputs"""
    
    # Valid trading symbols pattern (e.g., BTCUSDT, ETHUSDT)
    SYMBOL_PATTERN = re.compile(r'^[A-Z]{2,10}USDT$')
    
    # Valid order sides
    VALID_SIDES = ['BUY', 'SELL']
    
    # Valid order types
    VALID_ORDER_TYPES = ['MARKET', 'LIMIT', 'STOP', 'STOP_MARKET', 'TAKE_PROFIT', 'TAKE_PROFIT_MARKET']
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Validate trading symbol format"""
        if not isinstance(symbol, str):
            bot_logger.log_validation_error("symbol", symbol, "Must be a string")
            return False
        
        symbol = symbol.upper().strip()
        if not OrderValidator.SYMBOL_PATTERN.match(symbol):
            bot_logger.log_validation_error("symbol", symbol, "Invalid symbol format. Must end with USDT")
            return False
        
        return True
    
    @staticmethod
    def validate_side(side: str) -> bool:
        """Validate order side (BUY/SELL)"""
        if not isinstance(side, str):
            bot_logger.log_validation_error("side", side, "Must be a string")
            return False
        
        side = side.upper().strip()
        if side not in OrderValidator.VALID_SIDES:
            bot_logger.log_validation_error("side", side, f"Must be one of {OrderValidator.VALID_SIDES}")
            return False
        
        return True
    
    @staticmethod
    def validate_quantity(quantity: Union[str, float, int]) -> bool:
        """Validate order quantity"""
        try:
            qty = float(quantity)
            if qty <= 0:
                bot_logger.log_validation_error("quantity", quantity, "Must be greater than 0")
                return False
            
            if qty < Config.MIN_QUANTITY:
                bot_logger.log_validation_error("quantity", quantity, f"Must be at least {Config.MIN_QUANTITY}")
                return False
            
            if qty > Config.MAX_QUANTITY:
                bot_logger.log_validation_error("quantity", quantity, f"Must not exceed {Config.MAX_QUANTITY}")
                return False
            
            return True
            
        except (ValueError, TypeError):
            bot_logger.log_validation_error("quantity", quantity, "Must be a valid number")
            return False
    
    @staticmethod
    def validate_price(price: Union[str, float, int, None], required: bool = True) -> bool:
        """Validate order price"""
        if price is None:
            if required:
                bot_logger.log_validation_error("price", price, "Price is required for this order type")
                return False
            return True
        
        try:
            price_val = float(price)
            if price_val <= 0:
                bot_logger.log_validation_error("price", price, "Must be greater than 0")
                return False
            
            return True
            
        except (ValueError, TypeError):
            bot_logger.log_validation_error("price", price, "Must be a valid number")
            return False
    
    @staticmethod
    def validate_order_type(order_type: str) -> bool:
        """Validate order type"""
        if not isinstance(order_type, str):
            bot_logger.log_validation_error("order_type", order_type, "Must be a string")
            return False
        
        order_type = order_type.upper().strip()
        if order_type not in OrderValidator.VALID_ORDER_TYPES:
            bot_logger.log_validation_error("order_type", order_type, f"Must be one of {OrderValidator.VALID_ORDER_TYPES}")
            return False
        
        return True
    
    @staticmethod
    def validate_stop_price(stop_price: Union[str, float, int, None], required: bool = False) -> bool:
        """Validate stop price for stop orders"""
        if stop_price is None:
            if required:
                bot_logger.log_validation_error("stop_price", stop_price, "Stop price is required for stop orders")
                return False
            return True
        
        try:
            stop_val = float(stop_price)
            if stop_val <= 0:
                bot_logger.log_validation_error("stop_price", stop_price, "Must be greater than 0")
                return False
            
            return True
            
        except (ValueError, TypeError):
            bot_logger.log_validation_error("stop_price", stop_price, "Must be a valid number")
            return False
    
    @staticmethod
    def validate_time_in_force(time_in_force: Optional[str] = None) -> bool:
        """Validate time in force parameter"""
        valid_tif = ['GTC', 'IOC', 'FOK', 'GTX']
        
        if time_in_force is None:
            return True
        
        if not isinstance(time_in_force, str):
            bot_logger.log_validation_error("time_in_force", time_in_force, "Must be a string")
            return False
        
        tif = time_in_force.upper().strip()
        if tif not in valid_tif:
            bot_logger.log_validation_error("time_in_force", time_in_force, f"Must be one of {valid_tif}")
            return False
        
        return True
    
    @staticmethod
    def validate_market_order(symbol: str, side: str, quantity: Union[str, float, int]) -> bool:
        """Validate market order parameters"""
        return (OrderValidator.validate_symbol(symbol) and
                OrderValidator.validate_side(side) and
                OrderValidator.validate_quantity(quantity))
    
    @staticmethod
    def validate_limit_order(symbol: str, side: str, quantity: Union[str, float, int], 
                           price: Union[str, float, int]) -> bool:
        """Validate limit order parameters"""
        return (OrderValidator.validate_symbol(symbol) and
                OrderValidator.validate_side(side) and
                OrderValidator.validate_quantity(quantity) and
                OrderValidator.validate_price(price, required=True))
    
    @staticmethod
    def validate_stop_limit_order(symbol: str, side: str, quantity: Union[str, float, int],
                                price: Union[str, float, int], stop_price: Union[str, float, int]) -> bool:
        """Validate stop-limit order parameters"""
        return (OrderValidator.validate_symbol(symbol) and
                OrderValidator.validate_side(side) and
                OrderValidator.validate_quantity(quantity) and
                OrderValidator.validate_price(price, required=True) and
                OrderValidator.validate_stop_price(stop_price, required=True))
