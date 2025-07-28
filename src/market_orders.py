#!/usr/bin/env python3
"""
Market Orders Module for Binance Futures Order Bot
Usage: python src/market_orders.py BTCUSDT BUY 0.01
"""
import sys
import argparse
from typing import Dict, Any
from src.binance_client import BinanceFuturesClient
from src.validator import OrderValidator
from src.logger import bot_logger
from src.config import Config

class MarketOrderManager:
    """Handles market order operations"""
    
    def __init__(self):
        self.client = BinanceFuturesClient()
        bot_logger.info("Market Order Manager initialized")
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """
        Place a market order
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            
        Returns:
            Order response from Binance API
        """
        # Normalize inputs
        symbol = symbol.upper().strip()
        side = side.upper().strip()
        
        # Log order attempt
        bot_logger.log_order_attempt(
            order_type="MARKET",
            symbol=symbol,
            side=side,
            quantity=quantity
        )
        
        # Validate inputs
        if not OrderValidator.validate_market_order(symbol, side, quantity):
            raise ValueError("Invalid order parameters")
        
        try:
            # Check connectivity
            if not self.client.test_connectivity():
                raise ConnectionError("Unable to connect to Binance API")
            
            # Get current price for reference
            try:
                price_info = self.client.get_symbol_price(symbol)
                current_price = float(price_info['price'])
                bot_logger.info(f"Current {symbol} price: {current_price}")
            except Exception as e:
                bot_logger.warning(f"Could not fetch current price: {str(e)}")
                current_price = None
            
            # Prepare order parameters
            order_params = {
                'quantity': quantity,
                'timeInForce': 'GTC'  # Good Till Cancelled
            }
            
            # Place the order
            response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
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
                'order_type': 'MARKET'
            }
            bot_logger.log_order_error(e, order_details)
            raise
    
    def _display_order_summary(self, order_response: Dict[str, Any], current_price: float = None):
        """Display order summary to console"""
        print("\n" + "="*50)
        print("MARKET ORDER EXECUTED")
        print("="*50)
        print(f"Order ID: {order_response.get('orderId')}")
        print(f"Symbol: {order_response.get('symbol')}")
        print(f"Side: {order_response.get('side')}")
        print(f"Quantity: {order_response.get('origQty')}")
        print(f"Status: {order_response.get('status')}")
        print(f"Time in Force: {order_response.get('timeInForce')}")
        
        if current_price:
            print(f"Market Price: {current_price}")
        
        if order_response.get('fills'):
            print("\nFills:")
            total_qty = 0
            total_value = 0
            for fill in order_response['fills']:
                qty = float(fill['qty'])
                price = float(fill['price'])
                total_qty += qty
                total_value += qty * price
                print(f"  Qty: {qty}, Price: {price}")
            
            if total_qty > 0:
                avg_price = total_value / total_qty
                print(f"\nAverage Fill Price: {avg_price:.8f}")
        
        print("="*50)
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order status"""
        try:
            response = self.client.get_order(symbol, order_id)
            bot_logger.info(f"Retrieved order status for {symbol} order {order_id}")
            return response
        except Exception as e:
            bot_logger.error(f"Failed to get order status: {str(e)}")
            raise

def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(
        description='Place market orders on Binance Futures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/market_orders.py BTCUSDT BUY 0.01
  python src/market_orders.py ETHUSDT SELL 0.1
  python src/market_orders.py ADAUSDT BUY 100
        """
    )
    
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL', 'buy', 'sell'], 
                       help='Order side (BUY or SELL)')
    parser.add_argument('quantity', type=float, help='Order quantity')
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
        order_manager = MarketOrderManager()
        
        # Display configuration
        print(f"Using {'TESTNET' if Config.USE_TESTNET else 'PRODUCTION'} environment")
        print(f"Placing market order: {args.side} {args.quantity} {args.symbol}")
        
        # Confirm order in production
        if not Config.USE_TESTNET:
            confirm = input("WARNING: This is PRODUCTION trading! Continue? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Order cancelled by user")
                return
        
        # Place the order
        response = order_manager.place_market_order(
            symbol=args.symbol,
            side=args.side,
            quantity=args.quantity
        )
        
        print(f"\nOrder placed successfully!")
        print(f"Order ID: {response.get('orderId')}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        bot_logger.error(f"Market order failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
