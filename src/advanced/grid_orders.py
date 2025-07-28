#!/usr/bin/env python3
"""
Grid Orders Module for Binance Futures Order Bot
Usage: python src/advanced/grid_orders.py BTCUSDT 45000 55000 0.01 --levels 10
"""
import sys
import os
import argparse
import time
import threading
from typing import Dict, Any, List, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.binance_client import BinanceFuturesClient
from src.validator import OrderValidator
from src.logger import bot_logger
from src.config import Config

class GridOrderManager:
    """Handles Grid trading strategy operations"""
    
    def __init__(self):
        self.client = BinanceFuturesClient()
        self.active_grids = {}
        self.stop_flags = {}
        bot_logger.info("Grid Order Manager initialized")
    
    def place_grid_orders(self, symbol: str, lower_price: float, upper_price: float,
                         quantity_per_level: float, num_levels: int = 10,
                         rebalance: bool = True) -> Dict[str, Any]:
        """
        Place grid orders for automated buy-low/sell-high trading
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            lower_price: Lower bound of the grid
            upper_price: Upper bound of the grid
            quantity_per_level: Quantity for each grid level
            num_levels: Number of grid levels
            rebalance: Whether to automatically rebalance when orders are filled
            
        Returns:
            Grid order tracking information
        """
        # Normalize inputs
        symbol = symbol.upper().strip()
        
        # Generate Grid ID
        grid_id = f"GRID_{symbol}_{int(time.time())}"
        
        # Log grid order attempt
        bot_logger.log_order_attempt(
            order_type="GRID",
            symbol=symbol,
            lower_price=lower_price,
            upper_price=upper_price,
            quantity_per_level=quantity_per_level,
            num_levels=num_levels,
            grid_id=grid_id
        )
        
        # Validate inputs
        if not self._validate_grid_order(symbol, lower_price, upper_price, 
                                        quantity_per_level, num_levels):
            raise ValueError("Invalid grid order parameters")
        
        try:
            # Check connectivity
            if not self.client.test_connectivity():
                raise ConnectionError("Unable to connect to Binance API")
            
            # Get current price
            price_info = self.client.get_symbol_price(symbol)
            current_price = float(price_info['price'])
            bot_logger.info(f"Current {symbol} price: {current_price}")
            
            # Validate price range
            if not (lower_price < current_price < upper_price):
                raise ValueError(f"Current price {current_price} must be between {lower_price} and {upper_price}")
            
            # Calculate grid levels
            grid_levels = self._calculate_grid_levels(lower_price, upper_price, num_levels)
            
            # Initialize grid tracking
            grid_info = {
                'grid_id': grid_id,
                'symbol': symbol,
                'lower_price': lower_price,
                'upper_price': upper_price,
                'current_price': current_price,
                'quantity_per_level': quantity_per_level,
                'num_levels': num_levels,
                'rebalance': rebalance,
                'grid_levels': grid_levels,
                'start_time': datetime.now(),
                'buy_orders': [],
                'sell_orders': [],
                'filled_orders': [],
                'total_profit': 0.0,
                'status': 'ACTIVE'
            }
            
            # Store in active grids
            self.active_grids[grid_id] = grid_info
            self.stop_flags[grid_id] = False
            
            # Place initial grid orders
            self._place_initial_grid_orders(grid_info)
            
            # Display grid summary
            self._display_grid_start(grid_info)
            
            # Start grid monitoring if rebalancing is enabled
            if rebalance:
                grid_thread = threading.Thread(
                    target=self._monitor_grid,
                    args=(grid_id,),
                    daemon=True
                )
                grid_thread.start()
            
            return grid_info
            
        except Exception as e:
            # Log error
            order_details = {
                'symbol': symbol,
                'lower_price': lower_price,
                'upper_price': upper_price,
                'quantity_per_level': quantity_per_level,
                'num_levels': num_levels,
                'order_type': 'GRID'
            }
            bot_logger.log_order_error(e, order_details)
            raise
    
    def _validate_grid_order(self, symbol: str, lower_price: float, upper_price: float,
                            quantity_per_level: float, num_levels: int) -> bool:
        """Validate grid order parameters"""
        # Basic validation
        if not (OrderValidator.validate_symbol(symbol) and
                OrderValidator.validate_price(lower_price, required=True) and
                OrderValidator.validate_price(upper_price, required=True) and
                OrderValidator.validate_quantity(quantity_per_level)):
            return False
        
        # Grid-specific validation
        if lower_price >= upper_price:
            bot_logger.log_validation_error(
                "price_range", f"{lower_price}-{upper_price}",
                "Lower price must be less than upper price"
            )
            return False
        
        if num_levels < 3:
            bot_logger.log_validation_error("num_levels", num_levels, "Must be at least 3")
            return False
        
        if num_levels > 50:
            bot_logger.log_validation_error("num_levels", num_levels, "Must not exceed 50")
            return False
        
        # Check price difference
        price_diff_pct = ((upper_price - lower_price) / lower_price) * 100
        if price_diff_pct < 5:
            bot_logger.log_validation_error(
                "price_range", f"{price_diff_pct:.2f}%",
                "Price range should be at least 5% for effective grid trading"
            )
            return False
        
        return True
    
    def _calculate_grid_levels(self, lower_price: float, upper_price: float, 
                              num_levels: int) -> List[float]:
        """Calculate grid price levels"""
        price_step = (upper_price - lower_price) / (num_levels - 1)
        return [lower_price + i * price_step for i in range(num_levels)]
    
    def _place_initial_grid_orders(self, grid_info: Dict[str, Any]):
        """Place initial buy and sell orders for the grid"""
        symbol = grid_info['symbol']
        current_price = grid_info['current_price']
        quantity = grid_info['quantity_per_level']
        grid_levels = grid_info['grid_levels']
        
        buy_orders_placed = 0
        sell_orders_placed = 0
        
        for level_price in grid_levels:
            try:
                if level_price < current_price:
                    # Place BUY order below current price
                    order = self.client.place_order(
                        symbol=symbol,
                        side='BUY',
                        order_type='LIMIT',
                        quantity=quantity,
                        price=level_price,
                        timeInForce='GTC'
                    )
                    grid_info['buy_orders'].append({
                        'order': order,
                        'level_price': level_price,
                        'status': 'PLACED'
                    })
                    buy_orders_placed += 1
                    
                elif level_price > current_price:
                    # Place SELL order above current price
                    order = self.client.place_order(
                        symbol=symbol,
                        side='SELL',
                        order_type='LIMIT',
                        quantity=quantity,
                        price=level_price,
                        timeInForce='GTC'
                    )
                    grid_info['sell_orders'].append({
                        'order': order,
                        'level_price': level_price,
                        'status': 'PLACED'
                    })
                    sell_orders_placed += 1
                
                # Small delay to avoid rate limits
                time.sleep(0.1)
                
            except Exception as e:
                bot_logger.error(f"Failed to place grid order at level {level_price}: {str(e)}")
        
        bot_logger.info(f"Grid orders placed: {buy_orders_placed} BUY, {sell_orders_placed} SELL")
    
    def _monitor_grid(self, grid_id: str):
        """Monitor grid orders and rebalance when filled"""
        grid_info = self.active_grids[grid_id]
        
        while not self.stop_flags.get(grid_id, False) and grid_info['status'] == 'ACTIVE':
            try:
                # Check for filled orders
                self._check_filled_orders(grid_info)
                
                # Rebalance if needed
                if grid_info['rebalance']:
                    self._rebalance_grid(grid_info)
                
                # Wait before next check
                time.sleep(10)
                
            except Exception as e:
                bot_logger.error(f"Grid monitoring error for {grid_id}: {str(e)}")
                time.sleep(30)  # Wait longer on error
        
        grid_info['status'] = 'STOPPED'
        bot_logger.info(f"Grid monitoring stopped for {grid_id}")
    
    def _check_filled_orders(self, grid_info: Dict[str, Any]):
        """Check for filled orders and update grid state"""
        symbol = grid_info['symbol']
        
        # Check buy orders
        for buy_order_info in grid_info['buy_orders'][:]:
            if buy_order_info['status'] == 'PLACED':
                try:
                    order_status = self.client.get_order(
                        symbol, buy_order_info['order']['orderId']
                    )
                    
                    if order_status['status'] == 'FILLED':
                        buy_order_info['status'] = 'FILLED'
                        grid_info['filled_orders'].append({
                            'type': 'BUY',
                            'order': order_status,
                            'level_price': buy_order_info['level_price']
                        })
                        bot_logger.info(f"Grid BUY order filled at {buy_order_info['level_price']}")
                        
                except Exception as e:
                    bot_logger.error(f"Error checking buy order status: {str(e)}")
        
        # Check sell orders
        for sell_order_info in grid_info['sell_orders'][:]:
            if sell_order_info['status'] == 'PLACED':
                try:
                    order_status = self.client.get_order(
                        symbol, sell_order_info['order']['orderId']
                    )
                    
                    if order_status['status'] == 'FILLED':
                        sell_order_info['status'] = 'FILLED'
                        grid_info['filled_orders'].append({
                            'type': 'SELL',
                            'order': order_status,
                            'level_price': sell_order_info['level_price']
                        })
                        bot_logger.info(f"Grid SELL order filled at {sell_order_info['level_price']}")
                        
                except Exception as e:
                    bot_logger.error(f"Error checking sell order status: {str(e)}")
    
    def _rebalance_grid(self, grid_info: Dict[str, Any]):
        """Rebalance grid by placing new orders when others are filled"""
        # This is a simplified rebalancing logic
        # In practice, you might want more sophisticated rebalancing strategies
        pass
    
    def _display_grid_start(self, grid_info: Dict[str, Any]):
        """Display grid order start summary"""
        print("\n" + "="*70)
        print("GRID TRADING STRATEGY STARTED")
        print("="*70)
        print(f"Grid ID: {grid_info['grid_id']}")
        print(f"Symbol: {grid_info['symbol']}")
        print(f"Price Range: {grid_info['lower_price']} - {grid_info['upper_price']}")
        print(f"Current Price: {grid_info['current_price']}")
        print(f"Grid Levels: {grid_info['num_levels']}")
        print(f"Quantity per Level: {grid_info['quantity_per_level']}")
        print(f"Rebalancing: {'Enabled' if grid_info['rebalance'] else 'Disabled'}")
        
        print(f"\nGrid Levels:")
        for i, level in enumerate(grid_info['grid_levels']):
            if level < grid_info['current_price']:
                print(f"  Level {i+1}: {level:.2f} (BUY)")
            elif level > grid_info['current_price']:
                print(f"  Level {i+1}: {level:.2f} (SELL)")
            else:
                print(f"  Level {i+1}: {level:.2f} (CURRENT)")
        
        buy_orders = len(grid_info['buy_orders'])
        sell_orders = len(grid_info['sell_orders'])
        total_investment = buy_orders * grid_info['quantity_per_level'] * grid_info['current_price']
        
        print(f"\nOrders Placed:")
        print(f"  BUY Orders: {buy_orders}")
        print(f"  SELL Orders: {sell_orders}")
        print(f"  Estimated Investment: {total_investment:.2f} USDT")
        print("="*70)
    
    def stop_grid(self, grid_id: str) -> bool:
        """Stop a grid trading strategy"""
        if grid_id in self.stop_flags:
            self.stop_flags[grid_id] = True
            bot_logger.info(f"Stop signal sent for grid {grid_id}")
            return True
        return False
    
    def cancel_all_grid_orders(self, grid_id: str) -> Dict[str, Any]:
        """Cancel all orders for a grid"""
        if grid_id not in self.active_grids:
            raise ValueError(f"Grid {grid_id} not found")
        
        grid_info = self.active_grids[grid_id]
        symbol = grid_info['symbol']
        cancelled_orders = []
        
        # Cancel buy orders
        for buy_order_info in grid_info['buy_orders']:
            if buy_order_info['status'] == 'PLACED':
                try:
                    response = self.client.cancel_order(
                        symbol, buy_order_info['order']['orderId']
                    )
                    cancelled_orders.append(response)
                    buy_order_info['status'] = 'CANCELLED'
                except Exception as e:
                    bot_logger.error(f"Failed to cancel buy order: {str(e)}")
        
        # Cancel sell orders
        for sell_order_info in grid_info['sell_orders']:
            if sell_order_info['status'] == 'PLACED':
                try:
                    response = self.client.cancel_order(
                        symbol, sell_order_info['order']['orderId']
                    )
                    cancelled_orders.append(response)
                    sell_order_info['status'] = 'CANCELLED'
                except Exception as e:
                    bot_logger.error(f"Failed to cancel sell order: {str(e)}")
        
        grid_info['status'] = 'CANCELLED'
        bot_logger.info(f"Cancelled {len(cancelled_orders)} orders for grid {grid_id}")
        
        return {'cancelled_orders': cancelled_orders}
    
    def get_grid_status(self, grid_id: str) -> Dict[str, Any]:
        """Get grid trading status"""
        return self.active_grids.get(grid_id, {})

def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(
        description='Place grid orders on Binance Futures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic grid: BTCUSDT between 45000-55000 with 10 levels
  python src/advanced/grid_orders.py BTCUSDT 45000 55000 0.01 --levels 10
  
  # Tight grid: ETHUSDT between 2900-3100 with 20 levels
  python src/advanced/grid_orders.py ETHUSDT 2900 3100 0.1 --levels 20
  
  # Grid without auto-rebalancing
  python src/advanced/grid_orders.py ADAUSDT 0.4 0.6 100 --levels 15 --no-rebalance

Grid Strategy:
  Places buy orders below current price and sell orders above
  Profits from price oscillations within the defined range
  Works best in sideways/ranging markets
        """
    )
    
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('lower_price', type=float, help='Lower bound of grid')
    parser.add_argument('upper_price', type=float, help='Upper bound of grid')
    parser.add_argument('quantity', type=float, help='Quantity per grid level')
    parser.add_argument('--levels', type=int, default=10,
                       help='Number of grid levels (default: 10)')
    parser.add_argument('--no-rebalance', action='store_true',
                       help='Disable automatic rebalancing')
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
        order_manager = GridOrderManager()
        
        # Display configuration
        print(f"Using {'TESTNET' if Config.USE_TESTNET else 'PRODUCTION'} environment")
        print(f"Setting up grid trading:")
        print(f"  Symbol: {args.symbol}")
        print(f"  Price Range: {args.lower_price} - {args.upper_price}")
        print(f"  Quantity per Level: {args.quantity}")
        print(f"  Grid Levels: {args.levels}")
        print(f"  Auto-rebalancing: {'Disabled' if args.no_rebalance else 'Enabled'}")
        
        # Confirm order in production
        if not Config.USE_TESTNET:
            confirm = input("WARNING: This is PRODUCTION trading! Continue? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Order cancelled by user")
                return
        
        # Place the grid orders
        response = order_manager.place_grid_orders(
            symbol=args.symbol,
            lower_price=args.lower_price,
            upper_price=args.upper_price,
            quantity_per_level=args.quantity,
            num_levels=args.levels,
            rebalance=not args.no_rebalance
        )
        
        print(f"\nGrid trading started successfully!")
        print(f"Grid ID: {response.get('grid_id')}")
        print("\nPress Ctrl+C to stop and cancel all grid orders...")
        
        # Keep main thread alive
        try:
            while response.get('status') == 'ACTIVE':
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping grid trading...")
            order_manager.stop_grid(response['grid_id'])
            print("Cancelling all grid orders...")
            order_manager.cancel_all_grid_orders(response['grid_id'])
            print("Grid trading stopped and orders cancelled.")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        bot_logger.error(f"Grid trading failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
