#!/usr/bin/env python3
"""
Limit Orders Module for Binance Futures Order Bot
Usage: python src/limit_orders.py BTCUSDT BUY 0.01 50000
"""
import sys
import argparse
from typing import Dict, Any, Optional
from src.binance_client import BinanceFuturesClient
from src.validator import OrderValidator
from src.logger import bot_logger
from src.config import Config

class LimitOrderManager:
    """Handles limit order operations"""
    
    def __init__(self):
        self.client = BinanceFuturesClient()
        bot_logger.info("Limit Order Manager initialized")
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float,
                         time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        Place a limit order
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            price: Limit price
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
            order_type="LIMIT",
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            time_in_force=time_in_force
        )
        
        # Validate inputs
        if not OrderValidator.validate_limit_order(symbol, side, quantity, price):
            raise ValueError("Invalid order parameters")
        
        if not OrderValidator.validate_time_in_force(time_in_force):
            raise ValueError("Invalid time in force parameter")
        
        try:
            # Check connectivity
            if not self.client.test_connectivity():
                raise ConnectionError("Unable to connect to Binance API")
            
            # Get current price for comparison
            try:
                price_info = self.client.get_symbol_price(symbol)
                current_price = float(price_info['price'])
                bot_logger.info(f"Current {symbol} price: {current_price}")
                
                # Calculate price difference
                price_diff_pct = ((price - current_price) / current_price) * 100
                bot_logger.info(f"Limit price is {price_diff_pct:.2f}% {'above' if price_diff_pct > 0 else 'below'} current market price")
                
            except Exception as e:
                bot_logger.warning(f"Could not fetch current price: {str(e)}")
                current_price = None
                price_diff_pct = None
            
            # Prepare order parameters
            order_params = {
                'quantity': quantity,
                'price': price,
                'timeInForce': time_in_force
            }
            
            # Place the order
            response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                **order_params
            )
            
            # Log successful order
            bot_logger.log_order_success(response)
            
            # Display order summary
            self._display_order_summary(response, current_price, price_diff_pct)
            
            return response
            
        except Exception as e:
            # Log error
            order_details = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'order_type': 'LIMIT',
                'time_in_force': time_in_force
            }
            bot_logger.log_order_error(e, order_details)
            raise
    
    def _display_order_summary(self, order_response: Dict[str, Any], 
                              current_price: Optional[float] = None,
                              price_diff_pct: Optional[float] = None):
        """Display order summary to console"""
        print("\n" + "="*50)
        print("LIMIT ORDER PLACED")
        print("="*50)
        print(f"Order ID: {order_response.get('orderId')}")
        print(f"Symbol: {order_response.get('symbol')}")
        print(f"Side: {order_response.get('side')}")
        print(f"Quantity: {order_response.get('origQty')}")
        print(f"Limit Price: {order_response.get('price')}")
        print(f"Status: {order_response.get('status')}")
        print(f"Time in Force: {order_response.get('timeInForce')}")
        
        if current_price:
            print(f"Current Market Price: {current_price}")
        
        if price_diff_pct is not None:
            direction = "above" if price_diff_pct > 0 else "below"
            print(f"Price Difference: {abs(price_diff_pct):.2f}% {direction} market")
        
        # Order execution info
        if order_response.get('fills'):
            print("\nPartial Fills:")
            total_qty = 0
            total_value = 0
            for fill in order_response['fills']:
                qty = float(fill['qty'])
                fill_price = float(fill['price'])
                total_qty += qty
                total_value += qty * fill_price
                print(f"  Qty: {qty}, Price: {fill_price}")
            
            if total_qty > 0:
                avg_price = total_value / total_qty
                print(f"Average Fill Price: {avg_price:.8f}")
                remaining_qty = float(order_response.get('origQty', 0)) - total_qty
                print(f"Remaining Quantity: {remaining_qty}")
        
        print("="*50)
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel a limit order"""
        try:
            response = self.client.cancel_order(symbol, order_id)
            bot_logger.info(f"Cancelled order {order_id} for {symbol}")
            
            print(f"\nOrder {order_id} cancelled successfully")
            print(f"Symbol: {response.get('symbol')}")
            print(f"Original Quantity: {response.get('origQty')}")
            print(f"Executed Quantity: {response.get('executedQty')}")
            print(f"Status: {response.get('status')}")
            
            return response
        except Exception as e:
            bot_logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            raise
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order status"""
        try:
            response = self.client.get_order(symbol, order_id)
            bot_logger.info(f"Retrieved order status for {symbol} order {order_id}")
            
            print(f"\nOrder Status for {order_id}:")
            print(f"Symbol: {response.get('symbol')}")
            print(f"Status: {response.get('status')}")
            print(f"Side: {response.get('side')}")
            print(f"Original Quantity: {response.get('origQty')}")
            print(f"Executed Quantity: {response.get('executedQty')}")
            print(f"Price: {response.get('price')}")
            print(f"Time in Force: {response.get('timeInForce')}")
            
            return response
        except Exception as e:
            bot_logger.error(f"Failed to get order status: {str(e)}")
            raise
    
    def get_open_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get all open orders"""
        try:
            response = self.client.get_open_orders(symbol)
            bot_logger.info(f"Retrieved open orders for {symbol if symbol else 'all symbols'}")
            
            if not response:
                print("No open orders found")
                return response
            
            print(f"\nOpen Orders ({len(response)} total):")
            print("-" * 80)
            for order in response:
                print(f"ID: {order.get('orderId')} | "
                      f"{order.get('symbol')} | "
                      f"{order.get('side')} | "
                      f"Qty: {order.get('origQty')} | "
                      f"Price: {order.get('price')} | "
                      f"Status: {order.get('status')}")
            
            return response
        except Exception as e:
            bot_logger.error(f"Failed to get open orders: {str(e)}")
            raise

def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(
        description='Place limit orders on Binance Futures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/limit_orders.py BTCUSDT BUY 0.01 50000
  python src/limit_orders.py ETHUSDT SELL 0.1 3000 --tif IOC
  python src/limit_orders.py --cancel BTCUSDT 12345
  python src/limit_orders.py --status BTCUSDT 12345
  python src/limit_orders.py --list-open BTCUSDT
        """
    )
    
    # Main order arguments
    parser.add_argument('symbol', nargs='?', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', nargs='?', choices=['BUY', 'SELL', 'buy', 'sell'], 
                       help='Order side (BUY or SELL)')
    parser.add_argument('quantity', nargs='?', type=float, help='Order quantity')
    parser.add_argument('price', nargs='?', type=float, help='Limit price')
    
    # Optional parameters
    parser.add_argument('--tif', choices=['GTC', 'IOC', 'FOK'], default='GTC',
                       help='Time in force (default: GTC)')
    parser.add_argument('--testnet', action='store_true', 
                       help='Use testnet (default: True)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    # Order management commands
    parser.add_argument('--cancel', metavar='ORDER_ID', type=int,
                       help='Cancel order by ID (requires symbol)')
    parser.add_argument('--status', metavar='ORDER_ID', type=int,
                       help='Get order status by ID (requires symbol)')
    parser.add_argument('--list-open', action='store_true',
                       help='List all open orders (optionally for specific symbol)')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        bot_logger.logger.setLevel('DEBUG')
    
    try:
        # Initialize order manager
        order_manager = LimitOrderManager()
        
        # Display configuration
        print(f"Using {'TESTNET' if Config.USE_TESTNET else 'PRODUCTION'} environment")
        
        # Handle different commands
        if args.cancel:
            if not args.symbol:
                print("Error: Symbol required for cancel operation")
                sys.exit(1)
            print(f"Cancelling order {args.cancel} for {args.symbol}")
            order_manager.cancel_order(args.symbol, args.cancel)
            
        elif args.status:
            if not args.symbol:
                print("Error: Symbol required for status operation")
                sys.exit(1)
            order_manager.get_order_status(args.symbol, args.status)
            
        elif args.list_open:
            order_manager.get_open_orders(args.symbol)
            
        else:
            # Place new limit order
            if not all([args.symbol, args.side, args.quantity, args.price]):
                print("Error: symbol, side, quantity, and price are required for placing orders")
                parser.print_help()
                sys.exit(1)
            
            print(f"Placing limit order: {args.side} {args.quantity} {args.symbol} @ {args.price}")
            
            # Confirm order in production
            if not Config.USE_TESTNET:
                confirm = input("WARNING: This is PRODUCTION trading! Continue? (yes/no): ")
                if confirm.lower() != 'yes':
                    print("Order cancelled by user")
                    return
            
            # Place the order
            response = order_manager.place_limit_order(
                symbol=args.symbol,
                side=args.side,
                quantity=args.quantity,
                price=args.price,
                time_in_force=args.tif
            )
            
            print(f"\nOrder placed successfully!")
            print(f"Order ID: {response.get('orderId')}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        bot_logger.error(f"Limit order operation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
