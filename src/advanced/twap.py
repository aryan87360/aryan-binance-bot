#!/usr/bin/env python3
"""
TWAP (Time-Weighted Average Price) Orders Module for Binance Futures Order Bot
Usage: python src/advanced/twap.py BTCUSDT BUY 1.0 --chunks 10 --interval 60
"""
import sys
import os
import argparse
import time
import threading
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.binance_client import BinanceFuturesClient
from src.validator import OrderValidator
from src.logger import bot_logger
from src.config import Config

class TWAPOrderManager:
    """Handles TWAP (Time-Weighted Average Price) order operations"""
    
    def __init__(self):
        self.client = BinanceFuturesClient()
        self.active_twap_orders = {}
        self.stop_flags = {}
        bot_logger.info("TWAP Order Manager initialized")
    
    def place_twap_order(self, symbol: str, side: str, total_quantity: float,
                        num_chunks: int = 10, interval_seconds: int = 60,
                        price_limit: float = None, randomize: bool = True) -> Dict[str, Any]:
        """
        Place a TWAP order by splitting large order into smaller chunks over time
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            total_quantity: Total quantity to trade
            num_chunks: Number of chunks to split the order into
            interval_seconds: Time interval between chunks in seconds
            price_limit: Maximum price for BUY or minimum price for SELL (optional)
            randomize: Whether to randomize chunk timing (±20% of interval)
            
        Returns:
            TWAP order tracking information
        """
        # Normalize inputs
        symbol = symbol.upper().strip()
        side = side.upper().strip()
        
        # Generate TWAP ID
        twap_id = f"TWAP_{symbol}_{int(time.time())}"
        
        # Log TWAP order attempt
        bot_logger.log_order_attempt(
            order_type="TWAP",
            symbol=symbol,
            side=side,
            quantity=total_quantity,
            num_chunks=num_chunks,
            interval_seconds=interval_seconds,
            price_limit=price_limit,
            twap_id=twap_id
        )
        
        # Validate inputs
        if not self._validate_twap_order(symbol, side, total_quantity, num_chunks, interval_seconds):
            raise ValueError("Invalid TWAP order parameters")
        
        try:
            # Check connectivity
            if not self.client.test_connectivity():
                raise ConnectionError("Unable to connect to Binance API")
            
            # Calculate chunk size
            chunk_size = total_quantity / num_chunks
            
            # Get current price for analysis
            try:
                price_info = self.client.get_symbol_price(symbol)
                current_price = float(price_info['price'])
                bot_logger.info(f"Current {symbol} price: {current_price}")
            except Exception as e:
                bot_logger.warning(f"Could not fetch current price: {str(e)}")
                current_price = None
            
            # Validate price limit if provided
            if price_limit and current_price:
                self._validate_price_limit(side, current_price, price_limit)
            
            # Initialize TWAP tracking
            twap_info = {
                'twap_id': twap_id,
                'symbol': symbol,
                'side': side,
                'total_quantity': total_quantity,
                'chunk_size': chunk_size,
                'num_chunks': num_chunks,
                'interval_seconds': interval_seconds,
                'price_limit': price_limit,
                'randomize': randomize,
                'start_time': datetime.now(),
                'executed_chunks': 0,
                'executed_quantity': 0.0,
                'total_value': 0.0,
                'orders': [],
                'status': 'ACTIVE'
            }
            
            # Store in active orders
            self.active_twap_orders[twap_id] = twap_info
            self.stop_flags[twap_id] = False
            
            # Display TWAP summary
            self._display_twap_start(twap_info, current_price)
            
            # Start TWAP execution in background thread
            twap_thread = threading.Thread(
                target=self._execute_twap,
                args=(twap_id,),
                daemon=True
            )
            twap_thread.start()
            
            return twap_info
            
        except Exception as e:
            # Log error
            order_details = {
                'symbol': symbol,
                'side': side,
                'total_quantity': total_quantity,
                'num_chunks': num_chunks,
                'interval_seconds': interval_seconds,
                'order_type': 'TWAP'
            }
            bot_logger.log_order_error(e, order_details)
            raise
    
    def _validate_twap_order(self, symbol: str, side: str, total_quantity: float,
                            num_chunks: int, interval_seconds: int) -> bool:
        """Validate TWAP order parameters"""
        # Basic validation
        if not (OrderValidator.validate_symbol(symbol) and
                OrderValidator.validate_side(side) and
                OrderValidator.validate_quantity(total_quantity)):
            return False
        
        # TWAP-specific validation
        if num_chunks < 2:
            bot_logger.log_validation_error("num_chunks", num_chunks, "Must be at least 2")
            return False
        
        if num_chunks > 100:
            bot_logger.log_validation_error("num_chunks", num_chunks, "Must not exceed 100")
            return False
        
        if interval_seconds < 10:
            bot_logger.log_validation_error("interval_seconds", interval_seconds, "Must be at least 10 seconds")
            return False
        
        # Check chunk size
        chunk_size = total_quantity / num_chunks
        if chunk_size < Config.MIN_QUANTITY:
            bot_logger.log_validation_error(
                "chunk_size", chunk_size, 
                f"Chunk size {chunk_size} is below minimum {Config.MIN_QUANTITY}"
            )
            return False
        
        return True
    
    def _validate_price_limit(self, side: str, current_price: float, price_limit: float):
        """Validate price limit logic"""
        if side == 'BUY' and price_limit < current_price:
            bot_logger.warning(f"BUY price limit {price_limit} is below current price {current_price}")
        elif side == 'SELL' and price_limit > current_price:
            bot_logger.warning(f"SELL price limit {price_limit} is above current price {current_price}")
    
    def _execute_twap(self, twap_id: str):
        """Execute TWAP order chunks in background"""
        twap_info = self.active_twap_orders[twap_id]
        
        try:
            for chunk_num in range(twap_info['num_chunks']):
                # Check stop flag
                if self.stop_flags.get(twap_id, False):
                    bot_logger.info(f"TWAP {twap_id} stopped by user")
                    break
                
                # Calculate chunk details
                chunk_size = twap_info['chunk_size']
                remaining_quantity = twap_info['total_quantity'] - twap_info['executed_quantity']
                
                # Adjust last chunk to avoid rounding errors
                if chunk_num == twap_info['num_chunks'] - 1:
                    chunk_size = remaining_quantity
                
                # Execute chunk
                try:
                    chunk_result = self._execute_chunk(twap_info, chunk_num + 1, chunk_size)
                    
                    if chunk_result:
                        # Update TWAP info
                        twap_info['executed_chunks'] += 1
                        twap_info['executed_quantity'] += float(chunk_result.get('executedQty', chunk_size))
                        
                        # Calculate value if fills are available
                        if chunk_result.get('fills'):
                            chunk_value = sum(
                                float(fill['qty']) * float(fill['price']) 
                                for fill in chunk_result['fills']
                            )
                            twap_info['total_value'] += chunk_value
                        
                        twap_info['orders'].append(chunk_result)
                        
                        # Log chunk execution
                        bot_logger.info(f"TWAP {twap_id} chunk {chunk_num + 1}/{twap_info['num_chunks']} executed")
                
                except Exception as e:
                    bot_logger.error(f"TWAP {twap_id} chunk {chunk_num + 1} failed: {str(e)}")
                    # Continue with next chunk
                
                # Wait for next chunk (except for last chunk)
                if chunk_num < twap_info['num_chunks'] - 1:
                    wait_time = self._calculate_wait_time(twap_info)
                    time.sleep(wait_time)
            
            # Mark TWAP as completed
            twap_info['status'] = 'COMPLETED'
            twap_info['end_time'] = datetime.now()
            
            # Display completion summary
            self._display_twap_completion(twap_info)
            
        except Exception as e:
            twap_info['status'] = 'FAILED'
            twap_info['error'] = str(e)
            bot_logger.error(f"TWAP {twap_id} execution failed: {str(e)}")
    
    def _execute_chunk(self, twap_info: Dict[str, Any], chunk_num: int, chunk_size: float) -> Dict[str, Any]:
        """Execute a single TWAP chunk"""
        symbol = twap_info['symbol']
        side = twap_info['side']
        price_limit = twap_info.get('price_limit')
        
        try:
            # Check price limit if specified
            if price_limit:
                current_price_info = self.client.get_symbol_price(symbol)
                current_price = float(current_price_info['price'])
                
                if ((side == 'BUY' and current_price > price_limit) or
                    (side == 'SELL' and current_price < price_limit)):
                    bot_logger.warning(f"TWAP chunk {chunk_num} skipped due to price limit")
                    return None
            
            # Place market order for chunk
            order_result = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=chunk_size,
                timeInForce='GTC'
            )
            
            print(f"TWAP Chunk {chunk_num} executed: {chunk_size} {symbol} @ market price")
            
            return order_result
            
        except Exception as e:
            bot_logger.error(f"Failed to execute TWAP chunk {chunk_num}: {str(e)}")
            raise
    
    def _calculate_wait_time(self, twap_info: Dict[str, Any]) -> float:
        """Calculate wait time for next chunk with optional randomization"""
        base_interval = twap_info['interval_seconds']
        
        if twap_info.get('randomize', True):
            # Add ±20% randomization
            import random
            randomization_factor = random.uniform(0.8, 1.2)
            return base_interval * randomization_factor
        
        return base_interval
    
    def _display_twap_start(self, twap_info: Dict[str, Any], current_price: float = None):
        """Display TWAP order start summary"""
        print("\n" + "="*70)
        print("TWAP (TIME-WEIGHTED AVERAGE PRICE) ORDER STARTED")
        print("="*70)
        print(f"TWAP ID: {twap_info['twap_id']}")
        print(f"Symbol: {twap_info['symbol']}")
        print(f"Side: {twap_info['side']}")
        print(f"Total Quantity: {twap_info['total_quantity']}")
        print(f"Number of Chunks: {twap_info['num_chunks']}")
        print(f"Chunk Size: {twap_info['chunk_size']:.6f}")
        print(f"Interval: {twap_info['interval_seconds']} seconds")
        
        if current_price:
            print(f"Current Price: {current_price}")
        
        if twap_info.get('price_limit'):
            print(f"Price Limit: {twap_info['price_limit']}")
        
        total_duration = twap_info['num_chunks'] * twap_info['interval_seconds']
        print(f"Estimated Duration: {total_duration // 60}m {total_duration % 60}s")
        print("="*70)
    
    def _display_twap_completion(self, twap_info: Dict[str, Any]):
        """Display TWAP completion summary"""
        print("\n" + "="*70)
        print("TWAP ORDER COMPLETED")
        print("="*70)
        print(f"TWAP ID: {twap_info['twap_id']}")
        print(f"Executed Chunks: {twap_info['executed_chunks']}/{twap_info['num_chunks']}")
        print(f"Executed Quantity: {twap_info['executed_quantity']}/{twap_info['total_quantity']}")
        
        if twap_info['executed_quantity'] > 0 and twap_info['total_value'] > 0:
            avg_price = twap_info['total_value'] / twap_info['executed_quantity']
            print(f"Average Execution Price: {avg_price:.6f}")
        
        duration = twap_info.get('end_time', datetime.now()) - twap_info['start_time']
        print(f"Total Duration: {duration}")
        print("="*70)
    
    def stop_twap_order(self, twap_id: str) -> bool:
        """Stop an active TWAP order"""
        if twap_id in self.stop_flags:
            self.stop_flags[twap_id] = True
            bot_logger.info(f"Stop signal sent for TWAP {twap_id}")
            return True
        return False
    
    def get_twap_status(self, twap_id: str) -> Dict[str, Any]:
        """Get TWAP order status"""
        return self.active_twap_orders.get(twap_id, {})

def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(
        description='Place TWAP orders on Binance Futures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic TWAP: 1.0 BTC in 10 chunks over 10 minutes
  python src/advanced/twap.py BTCUSDT BUY 1.0 --chunks 10 --interval 60
  
  # TWAP with price limit
  python src/advanced/twap.py ETHUSDT SELL 5.0 --chunks 20 --interval 30 --price-limit 3000
  
  # Fast TWAP: 0.5 BTC in 5 chunks every 15 seconds
  python src/advanced/twap.py BTCUSDT BUY 0.5 --chunks 5 --interval 15

TWAP Strategy:
  Splits large orders into smaller chunks executed over time
  Helps reduce market impact and achieve better average prices
        """
    )
    
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL', 'buy', 'sell'], 
                       help='Order side (BUY or SELL)')
    parser.add_argument('quantity', type=float, help='Total order quantity')
    parser.add_argument('--chunks', type=int, default=10,
                       help='Number of chunks (default: 10)')
    parser.add_argument('--interval', type=int, default=60,
                       help='Interval between chunks in seconds (default: 60)')
    parser.add_argument('--price-limit', type=float,
                       help='Price limit (max for BUY, min for SELL)')
    parser.add_argument('--no-randomize', action='store_true',
                       help='Disable timing randomization')
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
        order_manager = TWAPOrderManager()
        
        # Display configuration
        print(f"Using {'TESTNET' if Config.USE_TESTNET else 'PRODUCTION'} environment")
        print(f"Placing TWAP order:")
        print(f"  {args.side} {args.quantity} {args.symbol}")
        print(f"  {args.chunks} chunks every {args.interval} seconds")
        if args.price_limit:
            print(f"  Price limit: {args.price_limit}")
        
        # Confirm order in production
        if not Config.USE_TESTNET:
            confirm = input("WARNING: This is PRODUCTION trading! Continue? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Order cancelled by user")
                return
        
        # Place the TWAP order
        response = order_manager.place_twap_order(
            symbol=args.symbol,
            side=args.side,
            total_quantity=args.quantity,
            num_chunks=args.chunks,
            interval_seconds=args.interval,
            price_limit=args.price_limit,
            randomize=not args.no_randomize
        )
        
        print(f"\nTWAP order started successfully!")
        print(f"TWAP ID: {response.get('twap_id')}")
        print("\nPress Ctrl+C to stop the TWAP order...")
        
        # Keep main thread alive
        try:
            while response.get('status') == 'ACTIVE':
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping TWAP order...")
            order_manager.stop_twap_order(response['twap_id'])
            time.sleep(2)  # Allow time for cleanup
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        bot_logger.error(f"TWAP order failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
