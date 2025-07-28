"""
Fear & Greed Index Analysis Module for Binance Futures Order Bot
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
from src.logger import bot_logger

class FearGreedAnalyzer:
    """Analyzes Fear & Greed Index data for market sentiment insights"""
    
    def __init__(self, data_file: str = "fear_greed_index.csv"):
        self.data_file = data_file
        self.data = None
        self.load_data()
    
    def load_data(self):
        """Load Fear & Greed Index data"""
        try:
            if os.path.exists(self.data_file):
                self.data = pd.read_csv(self.data_file)
                
                # Convert timestamp to datetime
                if 'timestamp' in self.data.columns:
                    self.data['datetime'] = pd.to_datetime(self.data['timestamp'], unit='s')
                
                # Ensure value is numeric
                if 'value' in self.data.columns:
                    self.data['value'] = pd.to_numeric(self.data['value'], errors='coerce')
                
                # Sort by date
                self.data = self.data.sort_values('datetime')
                
                bot_logger.info(f"Loaded {len(self.data)} Fear & Greed Index records")
            else:
                bot_logger.warning(f"Fear & Greed Index file {self.data_file} not found")
                self.data = pd.DataFrame()
                
        except Exception as e:
            bot_logger.error(f"Error loading Fear & Greed Index data: {str(e)}")
            self.data = pd.DataFrame()
    
    def get_current_sentiment(self) -> Dict[str, any]:
        """Get the most recent sentiment reading"""
        if self.data.empty:
            return {'value': None, 'classification': 'Unknown', 'date': None}
        
        try:
            latest = self.data.iloc[-1]
            return {
                'value': latest['value'],
                'classification': latest['classification'],
                'date': latest['datetime'].strftime('%Y-%m-%d'),
                'timestamp': latest['timestamp']
            }
        except Exception as e:
            bot_logger.error(f"Error getting current sentiment: {str(e)}")
            return {'value': None, 'classification': 'Unknown', 'date': None}
    
    def get_sentiment_trend(self, days: int = 30) -> Dict[str, any]:
        """Analyze sentiment trend over specified period"""
        if self.data.empty:
            return {}
        
        try:
            # Get data for the last N days
            cutoff_date = self.data['datetime'].max() - timedelta(days=days)
            recent_data = self.data[self.data['datetime'] >= cutoff_date]
            
            if recent_data.empty:
                return {}
            
            trend_analysis = {
                'period_days': days,
                'avg_sentiment': recent_data['value'].mean(),
                'min_sentiment': recent_data['value'].min(),
                'max_sentiment': recent_data['value'].max(),
                'sentiment_std': recent_data['value'].std(),
                'current_vs_avg': recent_data.iloc[-1]['value'] - recent_data['value'].mean(),
                'trend_direction': self._calculate_trend_direction(recent_data),
                'sentiment_distribution': self._get_sentiment_distribution(recent_data)
            }
            
            return trend_analysis
            
        except Exception as e:
            bot_logger.error(f"Error analyzing sentiment trend: {str(e)}")
            return {}
    
    def _calculate_trend_direction(self, data: pd.DataFrame) -> str:
        """Calculate the overall trend direction"""
        if len(data) < 2:
            return 'Insufficient data'
        
        try:
            # Simple linear regression to determine trend
            x = np.arange(len(data))
            y = data['value'].values
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 1:
                return 'Strongly Improving'
            elif slope > 0.5:
                return 'Improving'
            elif slope > -0.5:
                return 'Stable'
            elif slope > -1:
                return 'Declining'
            else:
                return 'Strongly Declining'
                
        except Exception:
            return 'Unknown'
    
    def _get_sentiment_distribution(self, data: pd.DataFrame) -> Dict[str, int]:
        """Get distribution of sentiment classifications"""
        try:
            distribution = data['classification'].value_counts().to_dict()
            return distribution
        except Exception:
            return {}
    
    def get_trading_signals(self) -> Dict[str, any]:
        """Generate trading signals based on Fear & Greed Index"""
        if self.data.empty:
            return {'signal': 'NEUTRAL', 'confidence': 0, 'reasoning': 'No data available'}
        
        try:
            current = self.get_current_sentiment()
            trend = self.get_sentiment_trend(30)
            
            current_value = current.get('value', 50)
            current_class = current.get('classification', 'Neutral')
            
            # Generate signals based on Fear & Greed levels
            signal_analysis = {
                'current_value': current_value,
                'current_classification': current_class,
                'signal': 'NEUTRAL',
                'confidence': 0,
                'reasoning': '',
                'suggested_strategy': '',
                'risk_level': 'MEDIUM'
            }
            
            # Extreme Fear (0-25) - Potential buying opportunity
            if current_value <= 25:
                signal_analysis.update({
                    'signal': 'BUY',
                    'confidence': min(90, 90 - current_value * 2),  # Higher confidence for lower values
                    'reasoning': 'Extreme fear indicates potential oversold conditions',
                    'suggested_strategy': 'DCA or limit orders below market',
                    'risk_level': 'HIGH'
                })
            
            # Fear (26-45) - Cautious buying
            elif current_value <= 45:
                signal_analysis.update({
                    'signal': 'WEAK_BUY',
                    'confidence': 60,
                    'reasoning': 'Fear sentiment suggests potential buying opportunity',
                    'suggested_strategy': 'Small position sizes with stop losses',
                    'risk_level': 'MEDIUM'
                })
            
            # Greed (55-75) - Caution advised
            elif current_value >= 75:
                signal_analysis.update({
                    'signal': 'SELL',
                    'confidence': min(90, current_value),
                    'reasoning': 'Extreme greed indicates potential overbought conditions',
                    'suggested_strategy': 'Take profits or short positions',
                    'risk_level': 'HIGH'
                })
            
            # Moderate greed (56-74) - Cautious selling
            elif current_value >= 56:
                signal_analysis.update({
                    'signal': 'WEAK_SELL',
                    'confidence': 50,
                    'reasoning': 'Greed sentiment suggests caution',
                    'suggested_strategy': 'Reduce position sizes or take partial profits',
                    'risk_level': 'MEDIUM'
                })
            
            # Neutral (46-55) - No strong signal
            else:
                signal_analysis.update({
                    'signal': 'NEUTRAL',
                    'confidence': 30,
                    'reasoning': 'Neutral sentiment provides no clear direction',
                    'suggested_strategy': 'Range trading or wait for clearer signals',
                    'risk_level': 'LOW'
                })
            
            # Adjust confidence based on trend
            if trend:
                trend_direction = trend.get('trend_direction', 'Unknown')
                if trend_direction in ['Strongly Improving', 'Improving'] and signal_analysis['signal'] in ['BUY', 'WEAK_BUY']:
                    signal_analysis['confidence'] = min(95, signal_analysis['confidence'] + 15)
                elif trend_direction in ['Strongly Declining', 'Declining'] and signal_analysis['signal'] in ['SELL', 'WEAK_SELL']:
                    signal_analysis['confidence'] = min(95, signal_analysis['confidence'] + 15)
            
            return signal_analysis
            
        except Exception as e:
            bot_logger.error(f"Error generating trading signals: {str(e)}")
            return {'signal': 'NEUTRAL', 'confidence': 0, 'reasoning': 'Error in analysis'}
    
    def get_historical_performance(self) -> Dict[str, any]:
        """Analyze historical performance of Fear & Greed signals"""
        if self.data.empty:
            return {}
        
        try:
            performance = {
                'total_periods': len(self.data),
                'extreme_fear_periods': len(self.data[self.data['value'] <= 25]),
                'fear_periods': len(self.data[(self.data['value'] > 25) & (self.data['value'] <= 45)]),
                'neutral_periods': len(self.data[(self.data['value'] > 45) & (self.data['value'] < 55)]),
                'greed_periods': len(self.data[(self.data['value'] >= 55) & (self.data['value'] < 75)]),
                'extreme_greed_periods': len(self.data[self.data['value'] >= 75]),
                'avg_value': self.data['value'].mean(),
                'value_std': self.data['value'].std(),
                'date_range': {
                    'start': self.data['datetime'].min().strftime('%Y-%m-%d'),
                    'end': self.data['datetime'].max().strftime('%Y-%m-%d')
                }
            }
            
            # Calculate percentages
            total = performance['total_periods']
            if total > 0:
                performance['percentages'] = {
                    'extreme_fear': (performance['extreme_fear_periods'] / total) * 100,
                    'fear': (performance['fear_periods'] / total) * 100,
                    'neutral': (performance['neutral_periods'] / total) * 100,
                    'greed': (performance['greed_periods'] / total) * 100,
                    'extreme_greed': (performance['extreme_greed_periods'] / total) * 100
                }
            
            return performance
            
        except Exception as e:
            bot_logger.error(f"Error analyzing historical performance: {str(e)}")
            return {}
    
    def get_sentiment_recommendations(self, order_type: str = None) -> List[str]:
        """Get specific recommendations based on current sentiment"""
        recommendations = []
        
        try:
            signals = self.get_trading_signals()
            signal = signals.get('signal', 'NEUTRAL')
            confidence = signals.get('confidence', 0)
            risk_level = signals.get('risk_level', 'MEDIUM')
            
            # General recommendations based on sentiment
            if signal == 'BUY' and confidence > 70:
                recommendations.extend([
                    "Strong buy signal detected - consider accumulating positions",
                    "Use DCA strategy to average into positions",
                    "Set tight stop losses due to high volatility in fear periods"
                ])
            elif signal == 'WEAK_BUY':
                recommendations.extend([
                    "Cautious buying opportunity - use small position sizes",
                    "Consider limit orders below current market price",
                    "Monitor for trend confirmation before increasing exposure"
                ])
            elif signal == 'SELL' and confidence > 70:
                recommendations.extend([
                    "Strong sell signal - consider taking profits",
                    "High greed levels suggest potential market top",
                    "Consider short positions with proper risk management"
                ])
            elif signal == 'WEAK_SELL':
                recommendations.extend([
                    "Caution advised - consider reducing position sizes",
                    "Take partial profits on existing long positions",
                    "Avoid FOMO trades in high greed periods"
                ])
            else:
                recommendations.extend([
                    "Neutral sentiment - no clear directional bias",
                    "Consider range trading strategies",
                    "Wait for clearer sentiment signals before major moves"
                ])
            
            # Order-type specific recommendations
            if order_type:
                if order_type.upper() == 'MARKET' and risk_level == 'HIGH':
                    recommendations.append("High risk period - consider limit orders instead of market orders")
                elif order_type.upper() == 'GRID' and signal == 'NEUTRAL':
                    recommendations.append("Neutral sentiment is ideal for grid trading strategies")
                elif order_type.upper() == 'TWAP' and risk_level == 'HIGH':
                    recommendations.append("High volatility period - TWAP strategy recommended for large orders")
            
            # Risk management recommendations
            if risk_level == 'HIGH':
                recommendations.extend([
                    "High risk environment - use smaller position sizes",
                    "Implement strict stop losses",
                    "Consider hedging strategies"
                ])
            
        except Exception as e:
            bot_logger.error(f"Error generating sentiment recommendations: {str(e)}")
            recommendations = ["Error analyzing sentiment - proceed with standard risk management"]
        
        return recommendations
    
    def display_sentiment_summary(self) -> str:
        """Generate a formatted summary of current sentiment analysis"""
        try:
            current = self.get_current_sentiment()
            signals = self.get_trading_signals()
            trend = self.get_sentiment_trend(30)
            
            summary = f"""
╔══════════════════════════════════════════════════════════════╗
║                    FEAR & GREED INDEX ANALYSIS               ║
╠══════════════════════════════════════════════════════════════╣
║ Current Value: {current.get('value', 'N/A'):>3} | {current.get('classification', 'Unknown'):<15} ║
║ Date: {current.get('date', 'N/A'):<10} | Signal: {signals.get('signal', 'NEUTRAL'):<8} ║
║ Confidence: {signals.get('confidence', 0):>3}% | Risk: {signals.get('risk_level', 'MEDIUM'):<6} ║
╠══════════════════════════════════════════════════════════════╣
║ 30-Day Trend: {trend.get('trend_direction', 'Unknown'):<15} ║
║ Average: {trend.get('avg_sentiment', 0):>6.1f} | Std: {trend.get('sentiment_std', 0):>6.1f} ║
╠══════════════════════════════════════════════════════════════╣
║ Reasoning: {signals.get('reasoning', 'No analysis available'):<40} ║
║ Strategy: {signals.get('suggested_strategy', 'No strategy suggested'):<41} ║
╚══════════════════════════════════════════════════════════════╝
            """
            
            return summary.strip()
            
        except Exception as e:
            bot_logger.error(f"Error generating sentiment summary: {str(e)}")
            return "Error generating sentiment summary"
