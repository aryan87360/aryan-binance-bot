# Binance Futures Order Bot

A comprehensive CLI-based trading bot for Binance USDT-M Futures that supports multiple order types with robust logging, validation, and documentation.

## Features

### Core Orders (Mandatory)
- ✅ **Market Orders** - Execute immediate buy/sell at current market price
- ✅ **Limit Orders** - Execute buy/sell at specified price with order management

### Advanced Orders (Bonus)
- ✅ **Stop-Limit Orders** - Trigger limit orders when stop price is hit
- ✅ **OCO (One-Cancels-the-Other)** - Place take-profit and stop-loss simultaneously
- ✅ **TWAP (Time-Weighted Average Price)** - Split large orders into smaller chunks over time
- ✅ **Grid Orders** - Automated buy-low/sell-high within a price range

### Analytics & Intelligence Features
- 📊 **Historical Data Analysis** - Trading pattern recognition and statistical insights
- 💭 **Fear & Greed Index Integration** - Market sentiment analysis for trading signals
- 🧠 **Enhanced Order Placement** - Analytics-driven position sizing and risk assessment
- 📈 **Real-time Dashboard** - Comprehensive analytics dashboard with market insights
- 🎯 **Smart Recommendations** - AI-driven trading suggestions based on data analysis

### Additional Features
- 🔒 **Input Validation** - Comprehensive validation for symbols, quantities, and prices
- 📊 **Structured Logging** - Detailed logs with timestamps and error traces in `bot.log`
- 🛡️ **Risk Management** - Built-in safety checks and position limits
- 🧪 **Testnet Support** - Safe testing environment before live trading
- 🎯 **CLI Interface** - Easy-to-use command-line interface for all order types

## Project Structure

```
BinanceFuturesOrderBot/
│
├── src/                          # All source code
│   ├── config.py                 # Configuration management
│   ├── logger.py                 # Structured logging utility
│   ├── validator.py              # Input validation
│   ├── binance_client.py         # Binance API client
│   ├── market_orders.py          # Market order logic
│   ├── limit_orders.py           # Limit order logic
│   ├── enhanced_market_orders.py # Enhanced orders with analytics
│   ├── data_analysis.py          # Historical data analysis
│   ├── fear_greed_analyzer.py    # Fear & Greed Index analysis
│   ├── analytics_dashboard.py    # Analytics dashboard
│   └── advanced/                 # Advanced order strategies
│       ├── stop_limit.py         # Stop-limit order logic
│       ├── oco.py                # OCO order logic
│       ├── twap.py               # TWAP strategy
│       └── grid_orders.py        # Grid trading strategy
│
├── main.py                       # Main CLI entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── historical_data.csv           # Historical trading data
├── fear_greed_index.csv          # Fear & Greed Index data
├── bot.log                       # Trading logs (generated)
├── README.md                     # This file
└── report.md                     # Analysis and documentation
```

## Installation & Setup

### 1. Clone or Download the Project
```bash
# If using git
git clone <repository-url>
cd BinanceFuturesOrderBot

# Or extract the zip file
unzip [your_name]_binance_bot.zip
cd BinanceFuturesOrderBot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. API Setup

#### Get Binance API Keys
1. Visit [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Create a new API key
3. Enable "Futures Trading" permission
4. **Important**: For testing, use [Binance Testnet](https://testnet.binancefuture.com/)

#### Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API credentials
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
USE_TESTNET=True  # Set to False for production
```

### 4. Verify Installation
```bash
# Test connectivity
python src/market_orders.py --help
```

## Usage Examples

### Market Orders
Execute immediate buy/sell at current market price:

```bash
# Buy 0.01 BTC at market price
python src/market_orders.py BTCUSDT BUY 0.01

# Sell 0.1 ETH at market price
python src/market_orders.py ETHUSDT SELL 0.1

# With verbose logging
python src/market_orders.py ADAUSDT BUY 100 --verbose
```

### Limit Orders
Execute buy/sell at specified price:

```bash
# Buy 0.01 BTC at $50,000
python src/limit_orders.py BTCUSDT BUY 0.01 50000

# Sell 0.1 ETH at $3,000 with IOC time-in-force
python src/limit_orders.py ETHUSDT SELL 0.1 3000 --tif IOC

# Check order status
python src/limit_orders.py --status BTCUSDT 12345

# Cancel an order
python src/limit_orders.py --cancel BTCUSDT 12345

# List open orders
python src/limit_orders.py --list-open BTCUSDT
```

### Stop-Limit Orders
Trigger limit orders when stop price is hit:

```bash
# BUY stop-limit (stop-loss for short position)
python src/advanced/stop_limit.py BTCUSDT BUY 0.01 51000 50000

# SELL stop-limit (stop-loss for long position)
python src/advanced/stop_limit.py BTCUSDT SELL 0.01 49000 50000

# With IOC time-in-force
python src/advanced/stop_limit.py ETHUSDT SELL 0.1 2900 3000 --tif IOC
```

### OCO Orders
Place take-profit and stop-loss simultaneously:

```bash
# SELL OCO (for closing long position with TP/SL)
python src/advanced/oco.py BTCUSDT SELL 0.01 52000 48000

# BUY OCO (for closing short position with TP/SL)
python src/advanced/oco.py BTCUSDT BUY 0.01 48000 52000

# With custom stop limit price
python src/advanced/oco.py ETHUSDT SELL 0.1 3200 2800 2750
```

### TWAP Orders
Split large orders into smaller chunks over time:

```bash
# Basic TWAP: 1.0 BTC in 10 chunks over 10 minutes
python src/advanced/twap.py BTCUSDT BUY 1.0 --chunks 10 --interval 60

# TWAP with price limit
python src/advanced/twap.py ETHUSDT SELL 5.0 --chunks 20 --interval 30 --price-limit 3000

# Fast TWAP: 0.5 BTC in 5 chunks every 15 seconds
python src/advanced/twap.py BTCUSDT BUY 0.5 --chunks 5 --interval 15
```

### Grid Orders
Automated buy-low/sell-high within a price range:

```bash
# Basic grid: BTCUSDT between 45000-55000 with 10 levels
python src/advanced/grid_orders.py BTCUSDT 45000 55000 0.01 --levels 10

# Tight grid: ETHUSDT between 2900-3100 with 20 levels
python src/advanced/grid_orders.py ETHUSDT 2900 3100 0.1 --levels 20

# Grid without auto-rebalancing
python src/advanced/grid_orders.py ADAUSDT 0.4 0.6 100 --levels 15 --no-rebalance
```

### Enhanced Orders with Analytics
Market orders with historical data analysis and sentiment integration:

```bash
# Enhanced market order with full analytics
python src/enhanced_market_orders.py BTCUSDT BUY 0.01 --with-analytics

# Enhanced order without analytics (same as regular market order)
python src/enhanced_market_orders.py ETHUSDT SELL 0.1 --no-analytics

# Using main CLI for enhanced orders
python main.py enhanced BTCUSDT BUY 0.01 --with-analytics
```

### Analytics Dashboard
Comprehensive market analysis and insights:

```bash
# Full analytics dashboard
python src/analytics_dashboard.py

# Symbol-specific analysis
python src/analytics_dashboard.py BTCUSDT

# Quick summary only
python src/analytics_dashboard.py --quick-summary

# Sentiment analysis only
python src/analytics_dashboard.py --sentiment-only

# Historical data analysis only
python src/analytics_dashboard.py --historical-only

# Using main CLI
python main.py analytics BTCUSDT
python main.py sentiment
```

### Main CLI Interface
Unified interface for all trading operations:

```bash
# Basic orders
python main.py market BTCUSDT BUY 0.01
python main.py limit ETHUSDT SELL 0.1 3000

# Advanced orders
python main.py stop-limit BTCUSDT SELL 0.01 49000 50000
python main.py oco BTCUSDT SELL 0.01 52000 48000
python main.py twap BTCUSDT BUY 1.0 --chunks 10 --interval 60
python main.py grid BTCUSDT 45000 55000 0.01 --levels 10

# Analytics and insights
python main.py analytics BTCUSDT
python main.py sentiment --signals-only
```

## Order Type Explanations

### Market Orders
- **Purpose**: Execute immediately at current market price
- **Use Case**: Quick entry/exit, high urgency trades
- **Risk**: Price slippage in volatile markets

### Limit Orders
- **Purpose**: Execute only at specified price or better
- **Use Case**: Precise price control, patient trading
- **Risk**: May not execute if price doesn't reach limit

### Stop-Limit Orders
- **Purpose**: Trigger limit order when stop price is reached
- **Use Case**: Stop-loss protection, breakout trading
- **Logic**: 
  - BUY: Triggers when price rises to stop price
  - SELL: Triggers when price falls to stop price

### OCO Orders
- **Purpose**: Place both take-profit and stop-loss orders
- **Use Case**: Risk management for existing positions
- **Logic**: When one order executes, manually cancel the other

### TWAP Orders
- **Purpose**: Reduce market impact of large orders
- **Use Case**: Large position building/unwinding
- **Strategy**: Splits order into smaller chunks over time

### Grid Orders
- **Purpose**: Profit from price oscillations in a range
- **Use Case**: Sideways/ranging markets
- **Strategy**: Places buy orders below and sell orders above current price

## Configuration

### Environment Variables
- `BINANCE_API_KEY`: Your Binance API key
- `BINANCE_API_SECRET`: Your Binance API secret
- `USE_TESTNET`: Use testnet (True) or production (False)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Risk Management Settings
- `MAX_POSITION_SIZE`: Maximum position size in USDT
- `MIN_QUANTITY`: Minimum order quantity
- `MAX_QUANTITY`: Maximum order quantity
- `STOP_LOSS_PERCENTAGE`: Default stop-loss percentage
- `TAKE_PROFIT_PERCENTAGE`: Default take-profit percentage

## Logging

All trading activities are logged to `bot.log` with structured JSON format:

```json
{
  "action": "ORDER_SUCCESS",
  "order_id": "12345",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": "0.01",
  "price": "50000",
  "status": "FILLED",
  "timestamp": "2024-01-01T12:00:00"
}
```

### Log Types
- `ORDER_ATTEMPT`: Order placement attempt
- `ORDER_SUCCESS`: Successful order placement
- `ORDER_ERROR`: Order placement error
- `VALIDATION_ERROR`: Input validation error
- `API_CALL`: API request/response logging

## Error Handling

The bot includes comprehensive error handling:

1. **Input Validation**: Validates all parameters before API calls
2. **API Error Handling**: Graceful handling of Binance API errors
3. **Network Issues**: Retry logic for connectivity problems
4. **Rate Limiting**: Automatic delays to avoid rate limits
5. **Logging**: All errors are logged with context

## Safety Features

1. **Testnet Default**: Uses testnet by default for safety
2. **Production Confirmation**: Requires explicit confirmation for production trading
3. **Input Validation**: Comprehensive parameter validation
4. **Position Limits**: Built-in position size limits
5. **Stop Signals**: Ability to stop long-running strategies (TWAP, Grid)

## Troubleshooting

### Common Issues

1. **API Key Errors**
   ```
   Error: API_KEY and API_SECRET must be set
   ```
   - Solution: Check your `.env` file and API key configuration

2. **Symbol Validation Errors**
   ```
   Error: Invalid symbol format
   ```
   - Solution: Use valid USDT futures symbols (e.g., BTCUSDT, ETHUSDT)

3. **Quantity Validation Errors**
   ```
   Error: Quantity below minimum
   ```
   - Solution: Check minimum quantity requirements for the symbol

4. **Connectivity Issues**
   ```
   Error: Unable to connect to Binance API
   ```
   - Solution: Check internet connection and API endpoint status

### Getting Help

1. Check the log file `bot.log` for detailed error information
2. Use `--verbose` flag for additional debugging output
3. Verify API key permissions and testnet/production settings
4. Ensure all dependencies are installed correctly

## Development

### Adding New Order Types
1. Create new module in `src/` or `src/advanced/`
2. Implement validation in `validator.py`
3. Add logging support using `logger.py`
4. Follow existing CLI patterns for consistency

### Testing
- Always test on testnet first
- Use small quantities for initial testing
- Monitor logs for any issues
- Verify order execution through Binance interface

## Disclaimer

⚠️ **Important**: This bot is for educational and testing purposes. Always:
- Test thoroughly on testnet before using real funds
- Start with small amounts
- Monitor your positions actively
- Understand the risks of automated trading
- Never risk more than you can afford to lose

Trading cryptocurrencies involves substantial risk and may not be suitable for all investors.

## License

This project is provided as-is for educational purposes. Use at your own risk.
