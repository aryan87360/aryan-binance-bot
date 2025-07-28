#!/usr/bin/env python3
"""
Stop-Limit Orders Module for Binance Futures Order Bot
Usage: python src/advanced/stop_limit.py BTCUSDT BUY 0.01 50000 49000
"""
import sys
import os
import argparse
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.binance_client import BinanceFuturesClient
from src.validator import OrderValidator
from src.logger import bot_logger
from src.config import Config

class StopLimitOrderManager:
    """Handles stop-limit order operations"""
    
    def __init__(self):
        self.client = BinanceFuturesClient()
        bot_logger.info("Stop-Limit Order Manager initialized")
    
    def place_stop_limit_order(self, symbol: str, side: str, quantity: float, 
                              price: float, stop_price: float, 
                              time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        Place a stop-limit order
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            price: Limit price (executed when stop is triggered)
            stop_price: Stop price (trigger price)
            time_in_force: Time in force ('GTC', 'IOC', 'FOK')
            
        Returns:
            Order response from Binance API
        """
        # Normalize inputs
        symbol = symbol.upper().strip()
        side = side.upper().strip()
        time_in_force = time_in_force.upper().strip()
        
        # Log order attempt
        bot_logger.log_order_attempt(
            order_type="STOP_LIMIT",
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force
        )
        
        # Validate inputs
        if not OrderValidator.validate_stop_limit_order(symbol, side, quantity, price, stop_price):
            raise ValueError("Invalid order parameters")
        
        if not OrderValidator.validate_time_in_force(time_in_force):
            raise ValueError("Invalid time in force parameter")
        
        # Validate stop-limit logic
        self._validate_stop_limit_logic(side, price, stop_price)
        
        try:
            # Check connectivity
            if not self.client.test_connectivity():
                raise ConnectionError("Unable to connect to Binance API")
            
            # Get current price for comparison
            try:
                price_info = self.client.get_symbol_price(symbol)
                current_price = float(price_info['price'])
                bot_logger.info(f"Current {symbol} price: {current_price}")
                
                # Analyze order setup
                self._analyze_stop_limit_setup(side, current_price, price, stop_price)
                
            except Exception as e:
                bot_logger.warning(f"Could not fetch current price: {str(e)}")
                current_price = None
            
            # Prepare order parameters
            order_params = {
                'quantity': quantity,
                'price': price,
                'stopPrice': stop_price,
                'timeInForce': time_in_force
            }
            
            # Place the order
            response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='STOP',
                **order_params
            )
            
            # Log successful order
            bot_logger.log_order_success(response)
            
            # Display order summary
            self._display_order_summary(response, current_price)
            
            return response
            
        except Exception as e:
            # Log error
            order_details = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'stop_price': stop_price,
                'order_type': 'STOP_LIMIT',
                'time_in_force': time_in_force
            }
            bot_logger.log_order_error(e, order_details)
            raise
    
    def _validate_stop_limit_logic(self, side: str, price: float, stop_price: float):
        """Validate stop-limit order logic"""
        if side == 'BUY':
            # For BUY stop-limit: stop_price should be above current market
            # and price should be >= stop_price (to ensure execution)
            if price < stop_price:
                raise ValueError("For BUY stop-limit: limit price should be >= stop price")
        else:  # SELL
            # For SELL stop-limit: stop_price should be below current market
            # and price should be <= stop_price (to ensure execution)
            if price > stop_price:
                raise ValueError("For SELL stop-limit: limit price should be <= stop price")
    
    def _analyze_stop_limit_setup(self, side: str, current_price: float, 
                                 price: float, stop_price: float):
        """Analyze and log stop-limit order setup"""
        stop_diff_pct = ((stop_price - current_price) / current_price) * 100
        price_diff_pct = ((price - current_price) / current_price) * 100
        
        if side == 'BUY':
            if stop_price <= current_price:
                bot_logger.warning(f"BUY stop-limit with stop price {stop_price} below current price {current_price} - will trigger immediately")
            else:
                bot_logger.info(f"BUY stop-limit: will trigger when price rises {stop_diff_pct:.2f}% to {stop_price}")
        else:  # SELL
            if stop_price >= current_price:
                bot_logger.warning(f"SELL stop-limit with stop price {stop_price} above current price {current_price} - will trigger immediately")
            else:
                bot_logger.info(f"SELL stop-limit: will trigger when price falls {abs(stop_diff_pct):.2f}% to {stop_price}")
        
        bot_logger.info(f"Limit price {price} is {price_diff_pct:.2f}% {'above' if price_diff_pct > 0 else 'below'} current market")
    
    def _display_order_summary(self, order_response: Dict[str, Any], current_price: float = None):
        """Display order summary to console"""
        print("\n" + "="*60)
        print("STOP-LIMIT ORDER PLACED")
        print("="*60)
        print(f"Order ID: {order_response.get('orderId')}")
        print(f"Symbol: {order_response.get('symbol')}")
        print(f"Side: {order_response.get('side')}")
        print(f"Quantity: {order_response.get('origQty')}")
        print(f"Stop Price: {order_response.get('stopPrice')} (trigger)")
        print(f"Limit Price: {order_response.get('price')} (execution)")
        print(f"Status: {order_response.get('status')}")
        print(f"Time in Force: {order_response.get('timeInForce')}")
        
        if current_price:
            print(f"Current Market Price: {current_price}")
            
            stop_price = float(order_response.get('stopPrice', 0))
            limit_price = float(order_response.get('price', 0))
            side = order_response.get('side')
            
            stop_diff = ((stop_price - current_price) / current_price) * 100
            limit_diff = ((limit_price - current_price) / current_price) * 100
            
            print(f"\nOrder Analysis:")
            if side == 'BUY':
                print(f"• Will trigger when price rises to {stop_price} ({stop_diff:+.2f}%)")
                print(f"• Will execute at limit price {limit_price} ({limit_diff:+.2f}%)")
            else:
                print(f"• Will trigger when price falls to {stop_price} ({stop_diff:+.2f}%)")
                print(f"• Will execute at limit price {limit_price} ({limit_diff:+.2f}%)")
        
        print("="*60)
        print("Note: This is a conditional order that will become active when the stop price is reached.")

def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(
        description='Place stop-limit orders on Binance Futures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # BUY stop-limit (stop-loss for short position)
  python src/advanced/stop_limit.py BTCUSDT BUY 0.01 51000 50000
  
  # SELL stop-limit (stop-loss for long position)  
  python src/advanced/stop_limit.py BTCUSDT SELL 0.01 49000 50000
  
  # With IOC time in force
  python src/advanced/stop_limit.py ETHUSDT SELL 0.1 2900 3000 --tif IOC

Stop-Limit Logic:
  BUY: Triggers when price rises to stop_price, then places limit order at price
  SELL: Triggers when price falls to stop_price, then places limit order at price
        """
    )
    
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL', 'buy', 'sell'], 
                       help='Order side (BUY or SELL)')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('price', type=float, help='Limit price (execution price)')
    parser.add_argument('stop_price', type=float, help='Stop price (trigger price)')
    parser.add_argument('--tif', choices=['GTC', 'IOC', 'FOK'], default='GTC',
                       help='Time in force (default: GTC)')
    parser.add_argument('--testnet', action='store_true', 
                       help='Use testnet (default: True)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        bot_logger.logger.setLevel('DEBUG')
    
    try:
        # Initialize order manager
        order_manager = StopLimitOrderManager()
        
        # Display configuration
        print(f"Using {'TESTNET' if Config.USE_TESTNET else 'PRODUCTION'} environment")
        print(f"Placing stop-limit order:")
        print(f"  {args.side} {args.quantity} {args.symbol}")
        print(f"  Stop Price: {args.stop_price} (trigger)")
        print(f"  Limit Price: {args.price} (execution)")
        
        # Confirm order in production
        if not Config.USE_TESTNET:
            confirm = input("WARNING: This is PRODUCTION trading! Continue? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Order cancelled by user")
                return
        
        # Place the order
        response = order_manager.place_stop_limit_order(
            symbol=args.symbol,
            side=args.side,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
            time_in_force=args.tif
        )
        
        print(f"\nStop-limit order placed successfully!")
        print(f"Order ID: {response.get('orderId')}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        bot_logger.error(f"Stop-limit order failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
