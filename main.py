#!/usr/bin/env python3
"""
Main CLI Entry Point for Binance Futures Order Bot with Analytics
Usage: python main.py [command] [options]
"""
import sys
import argparse
import subprocess
from pathlib import Path

def main():
    """Main CLI entry point with command routing"""
    parser = argparse.ArgumentParser(
        description='Binance Futures Order Bot - Multi-Strategy Trading CLI with Analytics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Commands:
  market         Place market orders
  enhanced       Place enhanced market orders with analytics
  limit          Place limit orders  
  stop-limit     Place stop-limit orders
  oco            Place OCO (One-Cancels-Other) orders
  twap           Execute TWAP (Time-Weighted Average Price) strategy
  grid           Execute Grid trading strategy
  analytics      Display analytics dashboard
  sentiment      Display Fear & Greed Index analysis

Examples:
  python main.py market BTCUSDT BUY 0.01
  python main.py enhanced BTCUSDT BUY 0.01 --with-analytics
  python main.py limit ETHUSDT SELL 0.1 3000
  python main.py stop-limit BTCUSDT SELL 0.01 49000 50000
  python main.py oco BTCUSDT SELL 0.01 52000 48000
  python main.py twap BTCUSDT BUY 1.0 --chunks 10 --interval 60
  python main.py grid BTCUSDT 45000 55000 0.01 --levels 10
  python main.py analytics BTCUSDT
  python main.py sentiment

For detailed help on each command:
  python main.py [command] --help
        """
    )
    
    # Add subparsers for different order types
    subparsers = parser.add_subparsers(dest='command', help='Order type commands')
    
    # Market orders
    market_parser = subparsers.add_parser('market', help='Place market orders')
    market_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    market_parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    market_parser.add_argument('quantity', type=float, help='Order quantity')
    market_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    # Enhanced market orders
    enhanced_parser = subparsers.add_parser('enhanced', help='Place enhanced market orders with analytics')
    enhanced_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    enhanced_parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    enhanced_parser.add_argument('quantity', type=float, help='Order quantity')
    enhanced_parser.add_argument('--with-analytics', action='store_true', default=True, help='Enable analytics (default)')
    enhanced_parser.add_argument('--no-analytics', action='store_true', help='Disable analytics')
    enhanced_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    # Limit orders
    limit_parser = subparsers.add_parser('limit', help='Place limit orders')
    limit_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    limit_parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    limit_parser.add_argument('quantity', type=float, help='Order quantity')
    limit_parser.add_argument('price', type=float, help='Limit price')
    limit_parser.add_argument('--tif', choices=['GTC', 'IOC', 'FOK'], default='GTC', help='Time in force')
    limit_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    # Stop-limit orders
    stop_parser = subparsers.add_parser('stop-limit', help='Place stop-limit orders')
    stop_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    stop_parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    stop_parser.add_argument('quantity', type=float, help='Order quantity')
    stop_parser.add_argument('price', type=float, help='Limit price')
    stop_parser.add_argument('stop_price', type=float, help='Stop price')
    stop_parser.add_argument('--tif', choices=['GTC', 'IOC', 'FOK'], default='GTC', help='Time in force')
    stop_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    # OCO orders
    oco_parser = subparsers.add_parser('oco', help='Place OCO orders')
    oco_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    oco_parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    oco_parser.add_argument('quantity', type=float, help='Order quantity')
    oco_parser.add_argument('take_profit_price', type=float, help='Take profit price')
    oco_parser.add_argument('stop_loss_price', type=float, help='Stop loss price')
    oco_parser.add_argument('stop_limit_price', type=float, nargs='?', help='Stop limit price (optional)')
    oco_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    # TWAP orders
    twap_parser = subparsers.add_parser('twap', help='Execute TWAP strategy')
    twap_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    twap_parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    twap_parser.add_argument('quantity', type=float, help='Total quantity')
    twap_parser.add_argument('--chunks', type=int, default=10, help='Number of chunks')
    twap_parser.add_argument('--interval', type=int, default=60, help='Interval in seconds')
    twap_parser.add_argument('--price-limit', type=float, help='Price limit')
    twap_parser.add_argument('--no-randomize', action='store_true', help='Disable randomization')
    twap_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    # Grid orders
    grid_parser = subparsers.add_parser('grid', help='Execute Grid strategy')
    grid_parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    grid_parser.add_argument('lower_price', type=float, help='Lower price bound')
    grid_parser.add_argument('upper_price', type=float, help='Upper price bound')
    grid_parser.add_argument('quantity', type=float, help='Quantity per level')
    grid_parser.add_argument('--levels', type=int, default=10, help='Number of levels')
    grid_parser.add_argument('--no-rebalance', action='store_true', help='Disable rebalancing')
    grid_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    # Analytics dashboard
    analytics_parser = subparsers.add_parser('analytics', help='Display analytics dashboard')
    analytics_parser.add_argument('symbol', nargs='?', help='Trading symbol (optional)')
    analytics_parser.add_argument('--quick-summary', action='store_true', help='Quick summary only')
    analytics_parser.add_argument('--sentiment-only', action='store_true', help='Sentiment analysis only')
    analytics_parser.add_argument('--historical-only', action='store_true', help='Historical analysis only')
    
    # Sentiment analysis
    sentiment_parser = subparsers.add_parser('sentiment', help='Display Fear & Greed Index analysis')
    sentiment_parser.add_argument('--trend-days', type=int, default=30, help='Days for trend analysis')
    sentiment_parser.add_argument('--signals-only', action='store_true', help='Trading signals only')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Route to appropriate module
    try:
        if args.command == 'market':
            cmd = ['python', 'src/market_orders.py', args.symbol, args.side, str(args.quantity)]
            if args.verbose:
                cmd.append('--verbose')
                
        elif args.command == 'enhanced':
            cmd = ['python', 'src/enhanced_market_orders.py', args.symbol, args.side, str(args.quantity)]
            if args.no_analytics:
                cmd.append('--no-analytics')
            elif args.with_analytics:
                cmd.append('--with-analytics')
            if args.verbose:
                cmd.append('--verbose')
                
        elif args.command == 'limit':
            cmd = ['python', 'src/limit_orders.py', args.symbol, args.side, str(args.quantity), str(args.price)]
            if args.tif != 'GTC':
                cmd.extend(['--tif', args.tif])
            if args.verbose:
                cmd.append('--verbose')
                
        elif args.command == 'stop-limit':
            cmd = ['python', 'src/advanced/stop_limit.py', args.symbol, args.side, 
                   str(args.quantity), str(args.price), str(args.stop_price)]
            if args.tif != 'GTC':
                cmd.extend(['--tif', args.tif])
            if args.verbose:
                cmd.append('--verbose')
                
        elif args.command == 'oco':
            cmd = ['python', 'src/advanced/oco.py', args.symbol, args.side, 
                   str(args.quantity), str(args.take_profit_price), str(args.stop_loss_price)]
            if args.stop_limit_price:
                cmd.append(str(args.stop_limit_price))
            if args.verbose:
                cmd.append('--verbose')
                
        elif args.command == 'twap':
            cmd = ['python', 'src/advanced/twap.py', args.symbol, args.side, str(args.quantity)]
            if args.chunks != 10:
                cmd.extend(['--chunks', str(args.chunks)])
            if args.interval != 60:
                cmd.extend(['--interval', str(args.interval)])
            if args.price_limit:
                cmd.extend(['--price-limit', str(args.price_limit)])
            if args.no_randomize:
                cmd.append('--no-randomize')
            if args.verbose:
                cmd.append('--verbose')
                
        elif args.command == 'grid':
            cmd = ['python', 'src/advanced/grid_orders.py', args.symbol, 
                   str(args.lower_price), str(args.upper_price), str(args.quantity)]
            if args.levels != 10:
                cmd.extend(['--levels', str(args.levels)])
            if args.no_rebalance:
                cmd.append('--no-rebalance')
            if args.verbose:
                cmd.append('--verbose')
                
        elif args.command == 'analytics':
            cmd = ['python', 'src/analytics_dashboard.py']
            if args.symbol:
                cmd.append(args.symbol)
            if args.quick_summary:
                cmd.append('--quick-summary')
            if args.sentiment_only:
                cmd.append('--sentiment-only')
            if args.historical_only:
                cmd.append('--historical-only')
                
        elif args.command == 'sentiment':
            cmd = ['python', 'src/analytics_dashboard.py', '--sentiment-only']
            if args.signals_only:
                # Use fear_greed_analyzer directly for signals only
                cmd = ['python', '-c', 
                       'from src.fear_greed_analyzer import FearGreedAnalyzer; '
                       'analyzer = FearGreedAnalyzer(); '
                       'signals = analyzer.get_trading_signals(); '
                       'print(f"Signal: {signals.get("signal", "NEUTRAL")} '
                       '(Confidence: {signals.get("confidence", 0)}%)"); '
                       'print(f"Risk: {signals.get("risk_level", "MEDIUM")}"); '
                       'print(f"Reasoning: {signals.get("reasoning", "N/A")}")']
            if hasattr(args, 'trend_days') and args.trend_days != 30:
                # For full sentiment analysis with custom trend days
                pass  # Dashboard handles this
        
        # Execute the command
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        sys.exit(result.returncode)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error executing command: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
