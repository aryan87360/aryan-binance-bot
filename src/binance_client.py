"""
Binance Futures API Client
"""
import hashlib
import hmac
import time
import requests
from typing import Dict, Any, Optional
from src.config import Config
from src.logger import bot_logger

class BinanceFuturesClient:
    """Binance Futures API Client with authentication and error handling"""
    
    def __init__(self):
        self.api_key = Config.API_KEY
        self.api_secret = Config.API_SECRET
        self.base_url = Config.get_api_url()
        
        # Validate configuration
        Config.validate_config()
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        })
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for API requests"""
        query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     signed: bool = False) -> Dict[str, Any]:
        """Make HTTP request to Binance API"""
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Log API call
            bot_logger.log_api_call(endpoint, method, params, response.status_code)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            bot_logger.error(f"API request failed: {str(e)}")
            raise
        except Exception as e:
            bot_logger.error(f"Unexpected error in API request: {str(e)}")
            raise
    
    def get_server_time(self) -> Dict[str, Any]:
        """Get server time"""
        return self._make_request('GET', '/time')
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange trading rules and symbol information"""
        return self._make_request('GET', '/exchangeInfo')
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        return self._make_request('GET', '/account', signed=True)
    
    def get_symbol_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price for a symbol"""
        params = {'symbol': symbol}
        return self._make_request('GET', '/ticker/price', params)
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book for a symbol"""
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/depth', params)
    
    def place_order(self, symbol: str, side: str, order_type: str, **kwargs) -> Dict[str, Any]:
        """Place a new order"""
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            **kwargs
        }
        return self._make_request('POST', '/order', params, signed=True)
    
    def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order information"""
        params = {'symbol': symbol, 'orderId': order_id}
        return self._make_request('GET', '/order', params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an order"""
        params = {'symbol': symbol, 'orderId': order_id}
        return self._make_request('DELETE', '/order', params, signed=True)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get all open orders"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/openOrders', params, signed=True)
    
    def get_position_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get position information"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/positionRisk', params, signed=True)
    
    def change_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Change leverage for a symbol"""
        params = {'symbol': symbol, 'leverage': leverage}
        return self._make_request('POST', '/leverage', params, signed=True)
    
    def test_connectivity(self) -> bool:
        """Test API connectivity"""
        try:
            response = self._make_request('GET', '/ping')
            return response == {}
        except Exception as e:
            bot_logger.error(f"Connectivity test failed: {str(e)}")
            return False
