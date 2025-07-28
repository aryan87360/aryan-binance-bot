#!/usr/bin/env python3
"""
OCO (One-Cancels-the-Other) Orders Module for Binance Futures Order Bot
Usage: python src/advanced/oco.py BTCUSDT SELL 0.01 52000 48000 47500
"""
import sys
import os
import argparse
import time
from typing import Dict, Any, List, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.binance_client import BinanceFuturesClient
from src.validator import OrderValidator
from src.logger import bot_logger
from src.config import Config

class OCOOrderManager:
    """Handles OCO (One-Cancels-the-Other) order operations"""
    
    def __init__(self):
        self.client = BinanceFuturesClient()
        bot_logger.info("OCO Order Manager initialized")
    
    def place_oco_order(self, symbol: str, side: str, quantity: float,
                       take_profit_price: float, stop_loss_price: float,
                       stop_limit_price: float = None) -> Dict[str, Any]:
        """
        Place an OCO order (Take Profit + Stop Loss)
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            take_profit_price: Take profit limit price
            stop_loss_price: Stop loss trigger price
            stop_limit_price: Stop limit execution price (optional, defaults to stop_loss_price)
            
        Returns:
            Dictionary containing both order responses
        """
        # Normalize inputs
        symbol = symbol.upper().strip()
        side = side.upper().strip()
        
        # Default stop limit price to stop loss price if not provided
        if stop_limit_price is None:
            stop_limit_price = stop_loss_price
        
        # Log OCO order attempt
        bot_logger.log_order_attempt(
            order_type="OCO",
            symbol=symbol,
            side=side,
            quantity=quantity,
            take_profit_price=take_profit_price,
            stop_loss_price=stop_loss_price,
            stop_limit_price=stop_limit_price
        )
        
        # Validate inputs
        if not self._validate_oco_order(symbol, side, quantity, take_profit_price, 
                                       stop_loss_price, stop_limit_price):
            raise ValueError("Invalid OCO order parameters")
        
        try:
            # Check connectivity
            if not self.client.test_connectivity():
                raise ConnectionError("Unable to connect to Binance API")
            
            # Get current price for analysis
            try:
                price_info = self.client.get_symbol_price(symbol)
                current_price = float(price_info['price'])
                bot_logger.info(f"Current {symbol} price: {current_price}")
                
                # Analyze OCO setup
                self._analyze_oco_setup(side, current_price, take_profit_price, 
                                      stop_loss_price, stop_limit_price)
                
            except Exception as e:
                bot_logger.warning(f"Could not fetch current price: {str(e)}")
                current_price = None
            
            # Since Binance Futures doesn't have native OCO, we simulate it
            # by placing both orders and managing them manually
            orders_result = self._place_simulated_oco(
                symbol, side, quantity, take_profit_price, 
                stop_loss_price, stop_limit_price
            )
            
            # Display OCO summary
            self._display_oco_summary(orders_result, current_price)
            
            return orders_result
            
        except Exception as e:
            # Log error
            order_details = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'take_profit_price': take_profit_price,
                'stop_loss_price': stop_loss_price,
                'stop_limit_price': stop_limit_price,
                'order_type': 'OCO'
            }
            bot_logger.log_order_error(e, order_details)
            raise
    
    def _validate_oco_order(self, symbol: str, side: str, quantity: float,
                           take_profit_price: float, stop_loss_price: float,
                           stop_limit_price: float) -> bool:
        """Validate OCO order parameters"""
        # Basic validation
        if not (OrderValidator.validate_symbol(symbol) and
                OrderValidator.validate_side(side) and
                OrderValidator.validate_quantity(quantity) and
                OrderValidator.validate_price(take_profit_price, required=True) and
                OrderValidator.validate_price(stop_loss_price, required=True) and
                OrderValidator.validate_price(stop_limit_price, required=True)):
            return False
        
        # OCO-specific validation
        if side == 'SELL':
            # For SELL OCO: take_profit should be below current, stop_loss above current
            if take_profit_price >= stop_loss_price:
                bot_logger.log_validation_error(
                    "oco_prices", 
                    f"TP:{take_profit_price}, SL:{stop_loss_price}",
                    "For SELL OCO: take profit price should be below stop loss price"
                )
                return False
        else:  # BUY
            # For BUY OCO: take_profit should be above current, stop_loss below current
            if take_profit_price <= stop_loss_price:
                bot_logger.log_validation_error(
                    "oco_prices",
                    f"TP:{take_profit_price}, SL:{stop_loss_price}",
                    "For BUY OCO: take profit price should be above stop loss price"
                )
                return False
        
        return True
    
    def _analyze_oco_setup(self, side: str, current_price: float,
                          take_profit_price: float, stop_loss_price: float,
                          stop_limit_price: float):
        """Analyze and log OCO order setup"""
        tp_diff_pct = ((take_profit_price - current_price) / current_price) * 100
        sl_diff_pct = ((stop_loss_price - current_price) / current_price) * 100
        
        bot_logger.info(f"OCO Analysis for {side} position:")
        bot_logger.info(f"Take Profit: {take_profit_price} ({tp_diff_pct:+.2f}% from current)")
        bot_logger.info(f"Stop Loss: {stop_loss_price} ({sl_diff_pct:+.2f}% from current)")
        
        # Calculate risk/reward ratio
        if side == 'SELL':
            profit_potential = abs(tp_diff_pct)
            loss_potential = abs(sl_diff_pct)
        else:  # BUY
            profit_potential = abs(tp_diff_pct)
            loss_potential = abs(sl_diff_pct)
        
        if loss_potential > 0:
            risk_reward_ratio = profit_potential / loss_potential
            bot_logger.info(f"Risk/Reward Ratio: {risk_reward_ratio:.2f}")
    
    def _place_simulated_oco(self, symbol: str, side: str, quantity: float,
                            take_profit_price: float, stop_loss_price: float,
                            stop_limit_price: float) -> Dict[str, Any]:
        """Place simulated OCO orders (since Binance Futures doesn't have native OCO)"""
        
        # Determine opposite side for take profit
        tp_side = 'SELL' if side == 'BUY' else 'BUY'
        sl_side = tp_side  # Same as take profit side
        
        orders_result = {
            'oco_id': f"OCO_{int(time.time())}",
            'symbol': symbol,
            'quantity': quantity,
            'orders': []
        }
        
        try:
            # Place Take Profit Limit Order
            tp_order = self.client.place_order(
                symbol=symbol,
                side=tp_side,
                order_type='LIMIT',
                quantity=quantity,
                price=take_profit_price,
                timeInForce='GTC'
            )
            
            orders_result['orders'].append({
                'type': 'TAKE_PROFIT',
                'order': tp_order
            })
            
            bot_logger.info(f"Take Profit order placed: ID {tp_order.get('orderId')}")
            
            # Small delay to avoid rate limits
            time.sleep(0.1)
            
            # Place Stop Loss Order
            sl_order = self.client.place_order(
                symbol=symbol,
                side=sl_side,
                order_type='STOP',
                quantity=quantity,
                stopPrice=stop_loss_price,
                price=stop_limit_price,
                timeInForce='GTC'
            )
            
            orders_result['orders'].append({
                'type': 'STOP_LOSS',
                'order': sl_order
            })
            
            bot_logger.info(f"Stop Loss order placed: ID {sl_order.get('orderId')}")
            
            # Log successful OCO placement
            bot_logger.log_order_success({
                'oco_id': orders_result['oco_id'],
                'symbol': symbol,
                'take_profit_order_id': tp_order.get('orderId'),
                'stop_loss_order_id': sl_order.get('orderId'),
                'status': 'OCO_PLACED'
            })
            
            return orders_result
            
        except Exception as e:
            # If second order fails, try to cancel the first one
            if len(orders_result['orders']) > 0:
                try:
                    first_order = orders_result['orders'][0]['order']
                    self.client.cancel_order(symbol, first_order.get('orderId'))
                    bot_logger.info(f"Cancelled first order due to OCO placement failure")
                except:
                    bot_logger.warning("Failed to cancel first order after OCO placement failure")
            raise
    
    def _display_oco_summary(self, orders_result: Dict[str, Any], current_price: float = None):
        """Display OCO order summary to console"""
        print("\n" + "="*70)
        print("OCO (ONE-CANCELS-THE-OTHER) ORDERS PLACED")
        print("="*70)
        print(f"OCO ID: {orders_result['oco_id']}")
        print(f"Symbol: {orders_result['symbol']}")
        print(f"Total Quantity: {orders_result['quantity']}")
        
        if current_price:
            print(f"Current Market Price: {current_price}")
        
        print("\nOrders Placed:")
        print("-" * 50)
        
        for order_info in orders_result['orders']:
            order_type = order_info['type']
            order = order_info['order']
            
            print(f"\n{order_type} ORDER:")
            print(f"  Order ID: {order.get('orderId')}")
            print(f"  Side: {order.get('side')}")
            print(f"  Quantity: {order.get('origQty')}")
            
            if order_type == 'TAKE_PROFIT':
                print(f"  Limit Price: {order.get('price')}")
            else:  # STOP_LOSS
                print(f"  Stop Price: {order.get('stopPrice')}")
                print(f"  Limit Price: {order.get('price')}")
            
            print(f"  Status: {order.get('status')}")
        
        print("\n" + "="*70)
        print("NOTE: These orders are managed separately. When one executes,")
        print("you should manually cancel the other to complete the OCO logic.")
        print("="*70)
    
    def cancel_oco_orders(self, symbol: str, oco_orders: List[int]) -> Dict[str, Any]:
        """Cancel all orders in an OCO setup"""
        results = []
        
        for order_id in oco_orders:
            try:
                response = self.client.cancel_order(symbol, order_id)
                results.append({
                    'order_id': order_id,
                    'status': 'CANCELLED',
                    'response': response
                })
                bot_logger.info(f"Cancelled OCO order {order_id}")
            except Exception as e:
                results.append({
                    'order_id': order_id,
                    'status': 'CANCEL_FAILED',
                    'error': str(e)
                })
                bot_logger.error(f"Failed to cancel OCO order {order_id}: {str(e)}")
        
        return {'cancelled_orders': results}

def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(
        description='Place OCO orders on Binance Futures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # SELL OCO (for closing long position with TP/SL)
  python src/advanced/oco.py BTCUSDT SELL 0.01 52000 48000
  
  # BUY OCO (for closing short position with TP/SL)
  python src/advanced/oco.py BTCUSDT BUY 0.01 48000 52000
  
  # With custom stop limit price
  python src/advanced/oco.py ETHUSDT SELL 0.1 3200 2800 2750

OCO Logic:
  Places both Take Profit (limit) and Stop Loss (stop-limit) orders
  When one executes, manually cancel the other to complete OCO
        """
    )
    
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL', 'buy', 'sell'], 
                       help='Order side (BUY or SELL)')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('take_profit_price', type=float, help='Take profit price')
    parser.add_argument('stop_loss_price', type=float, help='Stop loss trigger price')
    parser.add_argument('stop_limit_price', type=float, nargs='?', 
                       help='Stop limit execution price (optional, defaults to stop_loss_price)')
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
        order_manager = OCOOrderManager()
        
        # Display configuration
        print(f"Using {'TESTNET' if Config.USE_TESTNET else 'PRODUCTION'} environment")
        print(f"Placing OCO order:")
        print(f"  {args.side} {args.quantity} {args.symbol}")
        print(f"  Take Profit: {args.take_profit_price}")
        print(f"  Stop Loss: {args.stop_loss_price}")
        if args.stop_limit_price:
            print(f"  Stop Limit: {args.stop_limit_price}")
        
        # Confirm order in production
        if not Config.USE_TESTNET:
            confirm = input("WARNING: This is PRODUCTION trading! Continue? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Order cancelled by user")
                return
        
        # Place the OCO order
        response = order_manager.place_oco_order(
            symbol=args.symbol,
            side=args.side,
            quantity=args.quantity,
            take_profit_price=args.take_profit_price,
            stop_loss_price=args.stop_loss_price,
            stop_limit_price=args.stop_limit_price
        )
        
        print(f"\nOCO orders placed successfully!")
        print(f"OCO ID: {response.get('oco_id')}")
        
        # Display order IDs for reference
        order_ids = [order['order'].get('orderId') for order in response['orders']]
        print(f"Order IDs: {order_ids}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        bot_logger.error(f"OCO order failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
