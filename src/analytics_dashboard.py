#!/usr/bin/env python3
"""
Analytics Dashboard for Binance Futures Order Bot
Usage: python src/analytics_dashboard.py [symbol]
"""
import sys
import argparse
from typing import Dict, Any, Optional
from src.data_analysis import HistoricalDataAnalyzer
from src.fear_greed_analyzer import FearGreedAnalyzer
from src.binance_client import BinanceFuturesClient
from src.logger import bot_logger
from src.config import Config

class AnalyticsDashboard:
    """Comprehensive analytics dashboard for trading insights"""
    
    def __init__(self):
        self.data_analyzer = HistoricalDataAnalyzer()
        self.sentiment_analyzer = FearGreedAnalyzer()
        self.client = BinanceFuturesClient()
        bot_logger.info("Analytics Dashboard initialized")
    
    def display_full_dashboard(self, symbol: Optional[str] = None):
        """Display comprehensive analytics dashboard"""
        print("\n" + "="*80)
        print("📊 BINANCE FUTURES TRADING ANALYTICS DASHBOARD")
        print("="*80)
        
        # Market Overview
        self._display_market_overview(symbol)
        
        # Fear & Greed Analysis
        self._display_sentiment_analysis()
        
        # Historical Data Analysis
        self._display_historical_analysis(symbol)
        
        # Trading Recommendations
        self._display_trading_recommendations(symbol)
        
        print("="*80)
    
    def _display_market_overview(self, symbol: Optional[str] = None):
        """Display current market overview"""
        print("\n🌐 MARKET OVERVIEW")
        print("-" * 50)
        
        try:
            if symbol:
                # Get current price
                price_info = self.client.get_symbol_price(symbol)
                current_price = float(price_info['price'])
                
                # Get 24hr ticker stats
                ticker_url = f"{Config.get_api_url()}/ticker/24hr"
                ticker_params = {'symbol': symbol}
                
                print(f"Symbol: {symbol}")
                print(f"Current Price: ${current_price:,.4f}")
                
                # Get account info if possible
                try:
                    account_info = self.client.get_account_info()
                    total_balance = sum(float(asset['walletBalance']) for asset in account_info.get('assets', []))
                    print(f"Account Balance: ${total_balance:,.2f} USDT")
                except:
                    print("Account Balance: Unable to fetch")
            
            # Server time and connectivity
            server_time = self.client.get_server_time()
            print(f"Server Status: {'✅ Connected' if server_time else '❌ Disconnected'}")
            print(f"Environment: {'🧪 TESTNET' if Config.USE_TESTNET else '🔴 PRODUCTION'}")
            
        except Exception as e:
            print(f"❌ Error fetching market data: {str(e)}")
    
    def _display_sentiment_analysis(self):
        """Display Fear & Greed sentiment analysis"""
        print("\n💭 FEAR & GREED INDEX ANALYSIS")
        print("-" * 50)
        
        try:
            if self.sentiment_analyzer.data.empty:
                print("❌ No Fear & Greed Index data available")
                return
            
            # Current sentiment
            current = self.sentiment_analyzer.get_current_sentiment()
            signals = self.sentiment_analyzer.get_trading_signals()
            trend = self.sentiment_analyzer.get_sentiment_trend(30)
            
            # Display current reading
            value = current.get('value', 'N/A')
            classification = current.get('classification', 'Unknown')
            date = current.get('date', 'N/A')
            
            print(f"Current Reading: {value} ({classification})")
            print(f"Last Updated: {date}")
            
            # Display signal
            signal = signals.get('signal', 'NEUTRAL')
            confidence = signals.get('confidence', 0)
            risk_level = signals.get('risk_level', 'MEDIUM')
            
            signal_emoji = {
                'BUY': '🟢', 'WEAK_BUY': '🟡', 'NEUTRAL': '⚪', 
                'WEAK_SELL': '🟠', 'SELL': '🔴'
            }.get(signal, '⚪')
            
            print(f"Trading Signal: {signal_emoji} {signal} (Confidence: {confidence}%)")
            print(f"Risk Level: {risk_level}")
            
            # Display trend
            if trend:
                trend_direction = trend.get('trend_direction', 'Unknown')
                avg_sentiment = trend.get('avg_sentiment', 0)
                print(f"30-Day Trend: {trend_direction} (Avg: {avg_sentiment:.1f})")
            
            # Display reasoning
            reasoning = signals.get('reasoning', 'No reasoning available')
            print(f"Analysis: {reasoning}")
            
        except Exception as e:
            print(f"❌ Error in sentiment analysis: {str(e)}")
    
    def _display_historical_analysis(self, symbol: Optional[str] = None):
        """Display historical data analysis"""
        print("\n📈 HISTORICAL DATA ANALYSIS")
        print("-" * 50)
        
        try:
            if self.data_analyzer.data.empty:
                print("❌ No historical trading data available")
                return
            
            # Get comprehensive insights
            insights = self.data_analyzer.generate_trading_insights(symbol)
            
            # Price statistics
            price_stats = insights.get('price_statistics', {})
            if price_stats:
                print(f"Price Statistics:")
                print(f"  Mean: ${price_stats.get('mean_price', 0):.4f}")
                print(f"  Range: ${price_stats.get('min_price', 0):.4f} - ${price_stats.get('max_price', 0):.4f}")
                print(f"  Volatility: ${price_stats.get('std_price', 0):.4f}")
                print(f"  Total Trades: {price_stats.get('trade_count', 0)}")
            
            # Volume analysis
            volume_stats = insights.get('volume_analysis', {})
            if volume_stats:
                print(f"\nVolume Analysis:")
                print(f"  Total Volume: {volume_stats.get('total_volume', 0):.2f}")
                print(f"  Avg Trade Size: {volume_stats.get('avg_trade_size', 0):.4f}")
                
                if volume_stats.get('buy_sell_ratio'):
                    ratio = volume_stats['buy_sell_ratio']
                    bias = "Bullish" if ratio > 1.2 else "Bearish" if ratio < 0.8 else "Neutral"
                    print(f"  Buy/Sell Ratio: {ratio:.2f} ({bias})")
            
            # Support/Resistance levels
            sr_levels = insights.get('support_resistance', {})
            if sr_levels:
                support = sr_levels.get('support_levels', [])
                resistance = sr_levels.get('resistance_levels', [])
                
                if support:
                    print(f"\nSupport Levels: {', '.join([f'${level:.4f}' for level in support])}")
                if resistance:
                    print(f"Resistance Levels: {', '.join([f'${level:.4f}' for level in resistance])}")
            
            # Trading patterns
            patterns = insights.get('trading_patterns', {})
            if patterns:
                print(f"\nTrading Patterns:")
                if patterns.get('most_active_hour') is not None:
                    print(f"  Most Active Hour: {patterns['most_active_hour']}:00")
                if patterns.get('price_volatility'):
                    volatility_level = "High" if patterns['price_volatility'] > 0.05 else "Low"
                    print(f"  Volatility Level: {volatility_level}")
            
        except Exception as e:
            print(f"❌ Error in historical analysis: {str(e)}")
    
    def _display_trading_recommendations(self, symbol: Optional[str] = None):
        """Display comprehensive trading recommendations"""
        print("\n💡 TRADING RECOMMENDATIONS")
        print("-" * 50)
        
        try:
            recommendations = []
            
            # Get recommendations from both analyzers
            if not self.data_analyzer.data.empty:
                historical_insights = self.data_analyzer.generate_trading_insights(symbol)
                recommendations.extend(historical_insights.get('recommendations', []))
            
            if not self.sentiment_analyzer.data.empty:
                sentiment_recs = self.sentiment_analyzer.get_sentiment_recommendations()
                recommendations.extend(sentiment_recs)
            
            # Display recommendations
            if recommendations:
                for i, rec in enumerate(recommendations[:8], 1):  # Show top 8
                    print(f"  {i}. {rec}")
            else:
                print("  No specific recommendations available")
            
            # Strategy suggestions based on current conditions
            print(f"\n🎯 STRATEGY SUGGESTIONS:")
            
            # Get current sentiment signal
            if not self.sentiment_analyzer.data.empty:
                signals = self.sentiment_analyzer.get_trading_signals()
                signal = signals.get('signal', 'NEUTRAL')
                risk_level = signals.get('risk_level', 'MEDIUM')
                
                if signal in ['BUY', 'WEAK_BUY']:
                    print("  • Consider DCA (Dollar Cost Averaging) for gradual accumulation")
                    print("  • Use limit orders below current market price")
                elif signal in ['SELL', 'WEAK_SELL']:
                    print("  • Consider taking profits on existing long positions")
                    print("  • Use stop-loss orders to protect gains")
                else:
                    print("  • Range trading or grid strategies may be effective")
                    print("  • Wait for clearer directional signals")
                
                if risk_level == 'HIGH':
                    print("  • Use smaller position sizes due to high risk")
                    print("  • Implement tight stop-losses")
            
            # Volume-based suggestions
            if not self.data_analyzer.data.empty:
                volume_stats = self.data_analyzer.get_volume_analysis()
                avg_size = volume_stats.get('avg_trade_size', 0)
                
                if avg_size > 0:
                    print(f"  • Consider trade sizes around {avg_size:.4f} based on historical patterns")
                    if avg_size > 1.0:
                        print("  • For large orders, consider TWAP strategy to reduce market impact")
            
        except Exception as e:
            print(f"❌ Error generating recommendations: {str(e)}")
    
    def display_quick_summary(self, symbol: Optional[str] = None):
        """Display a quick summary for integration with other modules"""
        try:
            summary = {}
            
            # Get sentiment signal
            if not self.sentiment_analyzer.data.empty:
                signals = self.sentiment_analyzer.get_trading_signals()
                summary['sentiment'] = {
                    'signal': signals.get('signal', 'NEUTRAL'),
                    'confidence': signals.get('confidence', 0),
                    'risk_level': signals.get('risk_level', 'MEDIUM')
                }
            
            # Get key historical metrics
            if not self.data_analyzer.data.empty:
                insights = self.data_analyzer.generate_trading_insights(symbol)
                price_stats = insights.get('price_statistics', {})
                if price_stats:
                    volatility = price_stats.get('std_price', 0) / price_stats.get('mean_price', 1) if price_stats.get('mean_price', 0) > 0 else 0
                    summary['historical'] = {
                        'volatility': volatility,
                        'avg_price': price_stats.get('mean_price', 0),
                        'trade_count': price_stats.get('trade_count', 0)
                    }
            
            return summary
            
        except Exception as e:
            bot_logger.error(f"Error generating quick summary: {str(e)}")
            return {}

def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(
        description='Display analytics dashboard for Binance Futures trading',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/analytics_dashboard.py
  python src/analytics_dashboard.py BTCUSDT
  python src/analytics_dashboard.py --quick-summary
        """
    )
    
    parser.add_argument('symbol', nargs='?', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('--quick-summary', action='store_true',
                       help='Display quick summary only')
    parser.add_argument('--sentiment-only', action='store_true',
                       help='Display sentiment analysis only')
    parser.add_argument('--historical-only', action='store_true',
                       help='Display historical analysis only')
    
    args = parser.parse_args()
    
    try:
        dashboard = AnalyticsDashboard()
        
        if args.quick_summary:
            summary = dashboard.display_quick_summary(args.symbol)
            print("Quick Analytics Summary:")
            if summary.get('sentiment'):
                s = summary['sentiment']
                print(f"  Sentiment: {s['signal']} ({s['confidence']}% confidence, {s['risk_level']} risk)")
            if summary.get('historical'):
                h = summary['historical']
                print(f"  Historical: {h['trade_count']} trades, volatility {h['volatility']:.1%}")
        
        elif args.sentiment_only:
            print(dashboard.sentiment_analyzer.display_sentiment_summary())
        
        elif args.historical_only:
            dashboard._display_historical_analysis(args.symbol)
        
        else:
            dashboard.display_full_dashboard(args.symbol)
        
    except KeyboardInterrupt:
        print("\nDashboard closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {str(e)}")
        bot_logger.error(f"Analytics dashboard error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
