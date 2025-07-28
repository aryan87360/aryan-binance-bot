"""
Historical Data Analysis Module for Binance Futures Order Bot
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
from src.logger import bot_logger

class HistoricalDataAnalyzer:
    """Analyzes historical trading data for insights and patterns"""
    
    def __init__(self, data_file: str = "historical_data.csv"):
        self.data_file = data_file
        self.data = None
        self.load_data()
    
    def load_data(self):
        """Load historical trading data"""
        try:
            if os.path.exists(self.data_file):
                # Read the CSV with proper handling of the format
                self.data = pd.read_csv(self.data_file)
                
                # Clean and standardize column names
                if 'Execution Price' in self.data.columns:
                    self.data['price'] = pd.to_numeric(self.data['Execution Price'], errors='coerce')
                if 'Size Tokens' in self.data.columns:
                    self.data['quantity'] = pd.to_numeric(self.data['Size Tokens'], errors='coerce')
                if 'Size USD' in self.data.columns:
                    self.data['value_usd'] = pd.to_numeric(self.data['Size USD'], errors='coerce')
                if 'Side' in self.data.columns:
                    self.data['side'] = self.data['Side'].str.upper()
                if 'Timestamp IST' in self.data.columns:
                    self.data['timestamp'] = pd.to_datetime(self.data['Timestamp IST'], errors='coerce')
                
                # Remove rows with missing critical data
                self.data = self.data.dropna(subset=['price', 'quantity'])
                
                bot_logger.info(f"Loaded {len(self.data)} historical trading records")
            else:
                bot_logger.warning(f"Historical data file {self.data_file} not found")
                self.data = pd.DataFrame()
                
        except Exception as e:
            bot_logger.error(f"Error loading historical data: {str(e)}")
            self.data = pd.DataFrame()
    
    def get_price_statistics(self, symbol: str = None) -> Dict[str, float]:
        """Get price statistics from historical data"""
        if self.data.empty:
            return {}
        
        try:
            # Filter by symbol if provided (extract from Coin column)
            data = self.data.copy()
            if symbol and 'Coin' in data.columns:
                # Extract symbol from Coin column (e.g., "@107" might represent a specific token)
                data = data[data['Coin'].str.contains(symbol.replace('USDT', ''), case=False, na=False)]
            
            if data.empty:
                return {}
            
            stats = {
                'mean_price': data['price'].mean(),
                'median_price': data['price'].median(),
                'std_price': data['price'].std(),
                'min_price': data['price'].min(),
                'max_price': data['price'].max(),
                'price_range': data['price'].max() - data['price'].min(),
                'total_volume': data['quantity'].sum(),
                'total_value_usd': data['value_usd'].sum() if 'value_usd' in data.columns else 0,
                'trade_count': len(data)
            }
            
            # Calculate price percentiles
            stats.update({
                'price_25th': data['price'].quantile(0.25),
                'price_75th': data['price'].quantile(0.75),
                'price_90th': data['price'].quantile(0.90),
                'price_10th': data['price'].quantile(0.10)
            })
            
            return stats
            
        except Exception as e:
            bot_logger.error(f"Error calculating price statistics: {str(e)}")
            return {}
    
    def get_volume_analysis(self) -> Dict[str, float]:
        """Analyze trading volume patterns"""
        if self.data.empty:
            return {}
        
        try:
            volume_stats = {
                'total_volume': self.data['quantity'].sum(),
                'avg_trade_size': self.data['quantity'].mean(),
                'median_trade_size': self.data['quantity'].median(),
                'max_trade_size': self.data['quantity'].max(),
                'min_trade_size': self.data['quantity'].min(),
                'volume_std': self.data['quantity'].std()
            }
            
            # Analyze buy vs sell volume if side data is available
            if 'side' in self.data.columns:
                buy_data = self.data[self.data['side'] == 'BUY']
                sell_data = self.data[self.data['side'] == 'SELL']
                
                volume_stats.update({
                    'buy_volume': buy_data['quantity'].sum(),
                    'sell_volume': sell_data['quantity'].sum(),
                    'buy_count': len(buy_data),
                    'sell_count': len(sell_data),
                    'buy_sell_ratio': len(buy_data) / len(sell_data) if len(sell_data) > 0 else float('inf')
                })
            
            return volume_stats
            
        except Exception as e:
            bot_logger.error(f"Error analyzing volume: {str(e)}")
            return {}
    
    def get_trading_patterns(self) -> Dict[str, any]:
        """Identify trading patterns from historical data"""
        if self.data.empty:
            return {}
        
        try:
            patterns = {}
            
            # Time-based patterns
            if 'timestamp' in self.data.columns:
                self.data['hour'] = self.data['timestamp'].dt.hour
                self.data['day_of_week'] = self.data['timestamp'].dt.dayofweek
                
                # Most active trading hours
                hourly_volume = self.data.groupby('hour')['quantity'].sum()
                patterns['most_active_hour'] = hourly_volume.idxmax()
                patterns['least_active_hour'] = hourly_volume.idxmin()
                
                # Most active trading days (0=Monday, 6=Sunday)
                daily_volume = self.data.groupby('day_of_week')['quantity'].sum()
                patterns['most_active_day'] = daily_volume.idxmax()
                patterns['least_active_day'] = daily_volume.idxmin()
            
            # Price movement patterns
            if len(self.data) > 1:
                self.data = self.data.sort_values('timestamp') if 'timestamp' in self.data.columns else self.data
                price_changes = self.data['price'].pct_change().dropna()
                
                patterns.update({
                    'avg_price_change': price_changes.mean(),
                    'price_volatility': price_changes.std(),
                    'positive_moves': (price_changes > 0).sum(),
                    'negative_moves': (price_changes < 0).sum(),
                    'max_price_increase': price_changes.max(),
                    'max_price_decrease': price_changes.min()
                })
            
            return patterns
            
        except Exception as e:
            bot_logger.error(f"Error identifying trading patterns: {str(e)}")
            return {}
    
    def get_support_resistance_levels(self, symbol: str = None) -> Dict[str, List[float]]:
        """Identify potential support and resistance levels"""
        if self.data.empty:
            return {'support_levels': [], 'resistance_levels': []}
        
        try:
            data = self.data.copy()
            if symbol and 'Coin' in data.columns:
                data = data[data['Coin'].str.contains(symbol.replace('USDT', ''), case=False, na=False)]
            
            if data.empty:
                return {'support_levels': [], 'resistance_levels': []}
            
            prices = data['price'].values
            
            # Simple support/resistance identification using price clustering
            # Group prices into bins and find high-frequency price levels
            price_range = prices.max() - prices.min()
            num_bins = min(50, len(prices) // 10)  # Adaptive number of bins
            
            if num_bins < 5:
                return {'support_levels': [], 'resistance_levels': []}
            
            hist, bin_edges = np.histogram(prices, bins=num_bins)
            
            # Find bins with high frequency (potential S/R levels)
            threshold = np.percentile(hist, 80)  # Top 20% of frequency
            significant_bins = np.where(hist >= threshold)[0]
            
            # Convert bin indices to actual price levels
            support_resistance_levels = []
            for bin_idx in significant_bins:
                level = (bin_edges[bin_idx] + bin_edges[bin_idx + 1]) / 2
                support_resistance_levels.append(level)
            
            # Sort levels
            support_resistance_levels.sort()
            
            # Classify as support (lower prices) or resistance (higher prices)
            median_price = np.median(prices)
            support_levels = [level for level in support_resistance_levels if level < median_price]
            resistance_levels = [level for level in support_resistance_levels if level >= median_price]
            
            return {
                'support_levels': support_levels[-3:],  # Top 3 support levels
                'resistance_levels': resistance_levels[:3]  # Top 3 resistance levels
            }
            
        except Exception as e:
            bot_logger.error(f"Error identifying support/resistance levels: {str(e)}")
            return {'support_levels': [], 'resistance_levels': []}
    
    def generate_trading_insights(self, symbol: str = None) -> Dict[str, any]:
        """Generate comprehensive trading insights"""
        insights = {
            'price_statistics': self.get_price_statistics(symbol),
            'volume_analysis': self.get_volume_analysis(),
            'trading_patterns': self.get_trading_patterns(),
            'support_resistance': self.get_support_resistance_levels(symbol),
            'data_quality': {
                'total_records': len(self.data),
                'data_available': not self.data.empty,
                'date_range': self._get_date_range()
            }
        }
        
        # Generate recommendations based on analysis
        insights['recommendations'] = self._generate_recommendations(insights)
        
        return insights
    
    def _get_date_range(self) -> Dict[str, str]:
        """Get the date range of available data"""
        if self.data.empty or 'timestamp' not in self.data.columns:
            return {'start_date': 'N/A', 'end_date': 'N/A'}
        
        try:
            start_date = self.data['timestamp'].min().strftime('%Y-%m-%d')
            end_date = self.data['timestamp'].max().strftime('%Y-%m-%d')
            return {'start_date': start_date, 'end_date': end_date}
        except:
            return {'start_date': 'N/A', 'end_date': 'N/A'}
    
    def _generate_recommendations(self, insights: Dict) -> List[str]:
        """Generate trading recommendations based on analysis"""
        recommendations = []
        
        try:
            price_stats = insights.get('price_statistics', {})
            volume_stats = insights.get('volume_analysis', {})
            patterns = insights.get('trading_patterns', {})
            
            # Price-based recommendations
            if price_stats.get('std_price', 0) > 0:
                volatility = price_stats['std_price'] / price_stats.get('mean_price', 1)
                if volatility > 0.1:
                    recommendations.append("High volatility detected - consider using stop-loss orders")
                elif volatility < 0.02:
                    recommendations.append("Low volatility - grid trading strategy may be effective")
            
            # Volume-based recommendations
            if volume_stats.get('buy_sell_ratio'):
                ratio = volume_stats['buy_sell_ratio']
                if ratio > 1.5:
                    recommendations.append("Strong buying pressure observed - consider long positions")
                elif ratio < 0.67:
                    recommendations.append("Strong selling pressure observed - consider short positions")
            
            # Pattern-based recommendations
            if patterns.get('price_volatility', 0) > 0.05:
                recommendations.append("High price volatility - TWAP strategy recommended for large orders")
            
            if not recommendations:
                recommendations.append("Insufficient data for specific recommendations - use standard risk management")
            
        except Exception as e:
            bot_logger.error(f"Error generating recommendations: {str(e)}")
            recommendations = ["Error generating recommendations - proceed with caution"]
        
        return recommendations
