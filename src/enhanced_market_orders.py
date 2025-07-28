#!/usr/bin/env python3
"""
Enhanced Market Orders with Analytics and Sentiment Analysis
Usage: python src/enhanced_market_orders.py BTCUSDT BUY 0.01 --with-analytics
"""
import sys
import argparse
from typing import Dict, Any
from src.binance_client import BinanceFuturesClient
from src.validator import OrderValidator
from src.logger import bot_logger
from src.config import Config
from src.data_analysis import HistoricalDataAnalyzer
from src.fear_greed_analyzer import FearGreedAnalyzer

class EnhancedMarketOrderManager:
    """Enhanced Market Order Manager with analytics and sentiment analysis"""
    
    def __init__(self, use_analytics: bool = True):
        self.client = BinanceFuturesClient()
        self.use_analytics = use_analytics
        
        if use_analytics:
            self.data_analyzer = HistoricalDataAnalyzer()
            self.sentiment_analyzer = FearGreedAnalyzer()
        
        bot_logger.info("Enhanced Market Order Manager initialized")
    
    def place_market_order_with_analytics(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """
        Place a market order with enhanced analytics and sentiment analysis
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            
        Returns:
            Enhanced order response with analytics
        """
        # Normalize inputs
        symbol = symbol.upper().strip()
        side = side.upper().strip()
        
        # Pre-order analytics
        analytics_result = {}
        if self.use_analytics:
            analytics_result = self._perform_pre_order_analysis(symbol, side, quantity)
            
            # Display analytics summary
            self._display_analytics_summary(analytics_result)
            
            # Check for warnings
            warnings = analytics_result.get('warnings', [])
            if warnings:
                print("\n⚠️  ANALYTICS WARNINGS:")
                for warning in warnings:
                    print(f"   • {warning}")
                
                # Ask for confirmation if high-risk warnings
                high_risk_warnings = [w for w in warnings if 'high risk' in w.lower() or 'extreme' in w.lower()]
                if high_risk_warnings:
                    confirm = input("\nHigh risk conditions detected. Continue? (yes/no): ")
                    if confirm.lower() != 'yes':
                        print("Order cancelled due to risk warnings")
                        return {'status': 'CANCELLED', 'reason': 'User cancelled due to risk warnings'}
        
        # Log enhanced order attempt
        bot_logger.log_order_attempt(
            order_type="ENHANCED_MARKET",
            symbol=symbol,
            side=side,
            quantity=quantity,
            analytics_enabled=self.use_analytics,
            sentiment_signal=analytics_result.get('sentiment', {}).get('signal'),
            risk_level=analytics_result.get('sentiment', {}).get('risk_level')
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
            
            # Apply analytics-based adjustments
            adjusted_quantity = self._apply_analytics_adjustments(
                quantity, analytics_result, side
            )
            
            if adjusted_quantity != quantity:
                print(f"\n📊 Analytics Adjustment: Quantity adjusted from {quantity} to {adjusted_quantity}")
                quantity = adjusted_quantity
            
            # Prepare order parameters
            order_params = {
                'quantity': quantity,
                'timeInForce': 'GTC'
            }
            
            # Place the order
            response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                **order_params
            )
            
            # Enhance response with analytics
            enhanced_response = {
                **response,
                'analytics': analytics_result,
                'original_quantity': quantity if adjusted_quantity == quantity else adjusted_quantity,
                'price_at_order': current_price
            }
            
            # Log successful order
            bot_logger.log_order_success(enhanced_response)
            
            # Display enhanced order summary
            self._display_enhanced_order_summary(enhanced_response, analytics_result)
            
            return enhanced_response
            
        except Exception as e:
            # Log error
            order_details = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'order_type': 'ENHANCED_MARKET',
                'analytics_enabled': self.use_analytics
            }
            bot_logger.log_order_error(e, order_details)
            raise
    
    def _perform_pre_order_analysis(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """Perform comprehensive pre-order analysis"""
        analysis = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'timestamp': bot_logger.logger.handlers[0].formatter.formatTime(
                bot_logger.logger.makeRecord('', 0, '', 0, '', (), None)
            )
        }
        
        warnings = []
        recommendations = []
        
        try:
            # Historical data analysis
            if hasattr(self, 'data_analyzer') and not self.data_analyzer.data.empty:
                historical_insights = self.data_analyzer.generate_trading_insights(symbol)
                analysis['historical'] = historical_insights
                
                # Extract warnings from historical data
                price_stats = historical_insights.get('price_statistics', {})
                if price_stats.get('std_price', 0) > 0:
                    volatility = price_stats['std_price'] / price_stats.get('mean_price', 1)
                    if volatility > 0.15:
                        warnings.append("High historical volatility detected - consider smaller position sizes")
                
                recommendations.extend(historical_insights.get('recommendations', []))
            
            # Sentiment analysis
            if hasattr(self, 'sentiment_analyzer') and not self.sentiment_analyzer.data.empty:
                sentiment_signals = self.sentiment_analyzer.get_trading_signals()
                analysis['sentiment'] = sentiment_signals
                
                # Check sentiment alignment with order direction
                signal = sentiment_signals.get('signal', 'NEUTRAL')
                confidence = sentiment_signals.get('confidence', 0)
                risk_level = sentiment_signals.get('risk_level', 'MEDIUM')
                
                if side == 'BUY' and signal in ['SELL', 'WEAK_SELL'] and confidence > 60:
                    warnings.append(f"Sentiment analysis suggests {signal} but you're placing BUY order")
                elif side == 'SELL' and signal in ['BUY', 'WEAK_BUY'] and confidence > 60:
                    warnings.append(f"Sentiment analysis suggests {signal} but you're placing SELL order")
                
                if risk_level == 'HIGH':
                    warnings.append("High risk market conditions according to Fear & Greed Index")
                
                recommendations.extend(self.sentiment_analyzer.get_sentiment_recommendations('MARKET'))
            
            # Position sizing recommendations
            if quantity > 1.0:  # Large position warning
                warnings.append("Large position size detected - consider using TWAP strategy")
            
            analysis['warnings'] = warnings
            analysis['recommendations'] = recommendations
            
        except Exception as e:
            bot_logger.error(f"Error in pre-order analysis: {str(e)}")
            analysis['error'] = str(e)
        
        return analysis
    
    def _apply_analytics_adjustments(self, quantity: float, analytics: Dict[str, Any], side: str) -> float:
        """Apply analytics-based position size adjustments"""
        try:
            adjusted_quantity = quantity
            
            # Sentiment-based adjustments
            sentiment = analytics.get('sentiment', {})
            if sentiment:
                signal = sentiment.get('signal', 'NEUTRAL')
                confidence = sentiment.get('confidence', 0)
                risk_level = sentiment.get('risk_level', 'MEDIUM')
                
                # Reduce size in high-risk conditions
                if risk_level == 'HIGH':
                    adjusted_quantity *= 0.7  # Reduce by 30%
                
                # Adjust based on signal alignment
                if side == 'BUY':
                    if signal == 'SELL' and confidence > 70:
                        adjusted_quantity *= 0.5  # Significantly reduce contrarian trades
                    elif signal == 'BUY' and confidence > 80:
                        adjusted_quantity *= 1.2  # Slightly increase aligned trades
                elif side == 'SELL':
                    if signal == 'BUY' and confidence > 70:
                        adjusted_quantity *= 0.5
                    elif signal == 'SELL' and confidence > 80:
                        adjusted_quantity *= 1.2
            
            # Historical volatility adjustments
            historical = analytics.get('historical', {})
            if historical:
                price_stats = historical.get('price_statistics', {})
                if price_stats.get('std_price', 0) > 0:
                    volatility = price_stats['std_price'] / price_stats.get('mean_price', 1)
                    if volatility > 0.2:  # Very high volatility
                        adjusted_quantity *= 0.6
                    elif volatility > 0.1:  # High volatility
                        adjusted_quantity *= 0.8
            
            # Ensure minimum quantity requirements
            adjusted_quantity = max(adjusted_quantity, Config.MIN_QUANTITY)
            
            # Round to reasonable precision
            adjusted_quantity = round(adjusted_quantity, 6)
            
            return adjusted_quantity
            
        except Exception as e:
            bot_logger.error(f"Error applying analytics adjustments: {str(e)}")
            return quantity
    
    def _display_analytics_summary(self, analytics: Dict[str, Any]):
        """Display analytics summary before order placement"""
        print("\n" + "="*70)
        print("📊 PRE-ORDER ANALYTICS SUMMARY")
        print("="*70)
        
        # Sentiment analysis
        sentiment = analytics.get('sentiment', {})
        if sentiment:
            print(f"💭 Market Sentiment:")
            print(f"   Signal: {sentiment.get('signal', 'N/A')} (Confidence: {sentiment.get('confidence', 0)}%)")
            print(f"   Risk Level: {sentiment.get('risk_level', 'N/A')}")
            print(f"   Reasoning: {sentiment.get('reasoning', 'N/A')}")
        
        # Historical insights
        historical = analytics.get('historical', {})
        if historical:
            price_stats = historical.get('price_statistics', {})
            if price_stats:
                print(f"\n📈 Historical Analysis:")
                print(f"   Average Price: {price_stats.get('mean_price', 0):.4f}")
                print(f"   Price Range: {price_stats.get('min_price', 0):.4f} - {price_stats.get('max_price', 0):.4f}")
                print(f"   Volatility: {price_stats.get('std_price', 0):.4f}")
        
        # Recommendations
        recommendations = analytics.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations[:3]:  # Show top 3
                print(f"   • {rec}")
        
        print("="*70)
    
    def _display_enhanced_order_summary(self, order_response: Dict[str, Any], analytics: Dict[str, Any]):
        """Display enhanced order summary with analytics"""
        print("\n" + "="*70)
        print("✅ ENHANCED MARKET ORDER EXECUTED")
        print("="*70)
        print(f"Order ID: {order_response.get('orderId')}")
        print(f"Symbol: {order_response.get('symbol')}")
        print(f"Side: {order_response.get('side')}")
        print(f"Quantity: {order_response.get('origQty')}")
        print(f"Status: {order_response.get('status')}")
        
        # Analytics summary
        sentiment = analytics.get('sentiment', {})
        if sentiment:
            print(f"\n📊 Analytics at Execution:")
            print(f"   Sentiment Signal: {sentiment.get('signal', 'N/A')}")
            print(f"   Market Risk: {sentiment.get('risk_level', 'N/A')}")
        
        # Fill information
        if order_response.get('fills'):
            print(f"\n💰 Execution Details:")
            total_qty = 0
            total_value = 0
            for fill in order_response['fills']:
                qty = float(fill['qty'])
                price = float(fill['price'])
                total_qty += qty
                total_value += qty * price
                print(f"   Qty: {qty}, Price: {price}")
            
            if total_qty > 0:
                avg_price = total_value / total_qty
                print(f"   Average Fill Price: {avg_price:.8f}")
        
        print("="*70)

def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(
        description='Place enhanced market orders with analytics on Binance Futures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/enhanced_market_orders.py BTCUSDT BUY 0.01 --with-analytics
  python src/enhanced_market_orders.py ETHUSDT SELL 0.1 --no-analytics
  python src/enhanced_market_orders.py ADAUSDT BUY 100 --with-analytics --verbose
        """
    )
    
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL', 'buy', 'sell'], 
                       help='Order side (BUY or SELL)')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('--with-analytics', action='store_true', default=True,
                       help='Enable analytics and sentiment analysis (default)')
    parser.add_argument('--no-analytics', action='store_true',
                       help='Disable analytics and sentiment analysis')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        bot_logger.logger.setLevel('DEBUG')
    
    # Determine analytics usage
    use_analytics = args.with_analytics and not args.no_analytics
    
    try:
        # Initialize enhanced order manager
        order_manager = EnhancedMarketOrderManager(use_analytics=use_analytics)
        
        # Display configuration
        print(f"Using {'TESTNET' if Config.USE_TESTNET else 'PRODUCTION'} environment")
        print(f"Analytics: {'ENABLED' if use_analytics else 'DISABLED'}")
        print(f"Placing enhanced market order: {args.side} {args.quantity} {args.symbol}")
        
        # Confirm order in production
        if not Config.USE_TESTNET:
            confirm = input("WARNING: This is PRODUCTION trading! Continue? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Order cancelled by user")
                return
        
        # Place the enhanced order
        response = order_manager.place_market_order_with_analytics(
            symbol=args.symbol,
            side=args.side,
            quantity=args.quantity
        )
        
        if response.get('status') != 'CANCELLED':
            print(f"\n✅ Enhanced order executed successfully!")
            print(f"Order ID: {response.get('orderId')}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        bot_logger.error(f"Enhanced market order failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
