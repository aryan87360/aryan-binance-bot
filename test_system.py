#!/usr/bin/env python3
"""
System Test Script for Binance Futures Order Bot
Usage: python test_system.py
"""
import sys
import os
import subprocess
from pathlib import Path

def test_imports():
    """Test all module imports"""
    print("🧪 Testing module imports...")
    
    modules_to_test = [
        'src.config',
        'src.logger',
        'src.validator',
        'src.binance_client',
        'src.data_analysis',
        'src.fear_greed_analyzer'
    ]
    
    failed_imports = []
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {str(e)}")
            failed_imports.append(module)
    
    return len(failed_imports) == 0

def test_data_files():
    """Test data file availability"""
    print("\n📁 Testing data files...")
    
    required_files = [
        'historical_data.csv',
        'fear_greed_index.csv',
        'requirements.txt',
        '.env.example'
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - Missing")
            missing_files.append(file)
    
    return len(missing_files) == 0

def test_analytics_modules():
    """Test analytics modules functionality"""
    print("\n📊 Testing analytics modules...")
    
    try:
        # Test historical data analyzer
        from src.data_analysis import HistoricalDataAnalyzer
        analyzer = HistoricalDataAnalyzer()
        
        if not analyzer.data.empty:
            stats = analyzer.get_price_statistics()
            print(f"  ✅ Historical Data Analyzer - {len(analyzer.data)} records loaded")
        else:
            print("  ⚠️  Historical Data Analyzer - No data loaded")
        
        # Test Fear & Greed analyzer
        from src.fear_greed_analyzer import FearGreedAnalyzer
        sentiment_analyzer = FearGreedAnalyzer()
        
        if not sentiment_analyzer.data.empty:
            current = sentiment_analyzer.get_current_sentiment()
            print(f"  ✅ Fear & Greed Analyzer - Current sentiment: {current.get('classification', 'Unknown')}")
        else:
            print("  ⚠️  Fear & Greed Analyzer - No data loaded")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Analytics modules test failed: {str(e)}")
        return False

def test_cli_help():
    """Test CLI help commands"""
    print("\n🖥️  Testing CLI help commands...")
    
    commands_to_test = [
        ['python', 'main.py', '--help'],
        ['python', 'src/market_orders.py', '--help'],
        ['python', 'src/limit_orders.py', '--help'],
        ['python', 'src/enhanced_market_orders.py', '--help'],
        ['python', 'src/analytics_dashboard.py', '--help']
    ]
    
    failed_commands = []
    
    for cmd in commands_to_test:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  ✅ {' '.join(cmd)}")
            else:
                print(f"  ❌ {' '.join(cmd)} - Exit code: {result.returncode}")
                failed_commands.append(cmd)
        except Exception as e:
            print(f"  ❌ {' '.join(cmd)} - Error: {str(e)}")
            failed_commands.append(cmd)
    
    return len(failed_commands) == 0

def test_configuration():
    """Test configuration loading"""
    print("\n⚙️  Testing configuration...")
    
    try:
        from src.config import Config
        
        # Test basic config attributes
        required_attrs = ['API_KEY', 'API_SECRET', 'USE_TESTNET', 'LOG_LEVEL']
        missing_attrs = []
        
        for attr in required_attrs:
            if hasattr(Config, attr):
                print(f"  ✅ Config.{attr}")
            else:
                print(f"  ❌ Config.{attr} - Missing")
                missing_attrs.append(attr)
        
        # Test config methods
        try:
            base_url = Config.get_base_url()
            api_url = Config.get_api_url()
            print(f"  ✅ Config methods working")
            print(f"    Base URL: {base_url}")
            print(f"    API URL: {api_url}")
        except Exception as e:
            print(f"  ❌ Config methods failed: {str(e)}")
            return False
        
        return len(missing_attrs) == 0
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {str(e)}")
        return False

def test_validation():
    """Test input validation"""
    print("\n✅ Testing input validation...")
    
    try:
        from src.validator import OrderValidator
        
        # Test symbol validation
        valid_symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        invalid_symbols = ['BTC', 'INVALID', '']
        
        for symbol in valid_symbols:
            if OrderValidator.validate_symbol(symbol):
                print(f"  ✅ Valid symbol: {symbol}")
            else:
                print(f"  ❌ Should be valid: {symbol}")
                return False
        
        for symbol in invalid_symbols:
            if not OrderValidator.validate_symbol(symbol):
                print(f"  ✅ Invalid symbol rejected: {symbol}")
            else:
                print(f"  ❌ Should be invalid: {symbol}")
                return False
        
        # Test quantity validation
        if OrderValidator.validate_quantity(0.01):
            print(f"  ✅ Valid quantity: 0.01")
        else:
            print(f"  ❌ Should be valid quantity: 0.01")
            return False
        
        if not OrderValidator.validate_quantity(-1):
            print(f"  ✅ Invalid quantity rejected: -1")
        else:
            print(f"  ❌ Should be invalid quantity: -1")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Validation test failed: {str(e)}")
        return False

def test_logging():
    """Test logging functionality"""
    print("\n📝 Testing logging...")
    
    try:
        from src.logger import bot_logger
        
        # Test basic logging
        bot_logger.info("Test info message")
        bot_logger.warning("Test warning message")
        bot_logger.error("Test error message")
        
        # Test structured logging
        bot_logger.log_order_attempt("TEST", "BTCUSDT", "BUY", 0.01)
        
        print("  ✅ Basic logging functions")
        print("  ✅ Structured logging functions")
        
        # Check if log file exists
        if os.path.exists('bot.log'):
            print("  ✅ Log file created")
        else:
            print("  ⚠️  Log file not found")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Logging test failed: {str(e)}")
        return False

def generate_test_report():
    """Generate comprehensive test report"""
    print("\n" + "="*60)
    print("🧪 BINANCE FUTURES ORDER BOT - SYSTEM TEST REPORT")
    print("="*60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Data Files", test_data_files),
        ("Configuration", test_configuration),
        ("Input Validation", test_validation),
        ("Logging System", test_logging),
        ("Analytics Modules", test_analytics_modules),
        ("CLI Help Commands", test_cli_help)
    ]
    
    results = {}
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed_tests += 1
        except Exception as e:
            print(f"  ❌ Test failed with exception: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! System is ready for use.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    print("\n💡 Next Steps:")
    print("1. Set up your .env file with Binance API credentials")
    print("2. Test on Binance Testnet first")
    print("3. Start with small amounts for live trading")
    print("4. Monitor logs in bot.log for any issues")
    
    return passed_tests == total_tests

def main():
    """Main test execution"""
    try:
        # Change to script directory
        os.chdir(Path(__file__).parent)
        
        # Run comprehensive tests
        success = generate_test_report()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
