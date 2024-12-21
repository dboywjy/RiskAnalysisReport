import websocket
import json
import requests
import pandas as pd
from io import StringIO
import time
from datetime import datetime
import os

class StockDataFetcher:
    def __init__(self, item, start_date, end_date, period='D'):
        # WebSocket and API URLs
        self.ws_url = ""
        self.auth_url = ""
        self.historical_data_url = ""
        
        # Data fetching parameters
        self.item = item
        self.start_date = start_date
        self.end_date = end_date
        self.period = period
        self.data_fetched = False
        
        # Validate dates
        self._validate_dates()
        
    def _validate_dates(self):
        """Validate date formats"""
        try:
            datetime.strptime(self.start_date, '%Y-%m-%d')
            datetime.strptime(self.end_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Dates must be in YYYY-MM-DD format")
            
    def get_auth_key(self):
        """Obtain AuthKey"""
        data = {
            "SiteID": "",
            "ProdID": "RR"
        }
        response = requests.post(self.auth_url, data=data)
        if response.status_code == 200:
            return response.text.strip()
        else:
            print(f"Error getting AuthKey: {response.status_code}")
            return None

    def fetch_historical_data(self, seckey):
        """Fetch historical data for the item"""
        params = {
            "item": self.item,
            "period": self.period,
            "from": self.start_date,
            "to": self.end_date,
            "seckey": seckey
        }
        
        response = requests.get(self.historical_data_url, params=params)
        
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            df = df[df['Volume'] > 0]
            # df['Date'] = pd.to_datetime(df['Date'], unit='ms').dt.strftime("%Y-%m-%d")
            output_file = f'./inputData/{self.item}_{self.start_date}_{self.end_date}_{self.period}.json'
            df.to_json(output_file, orient="records", force_ascii=False, indent=4)
            print(f"Historical data for {self.item} saved to '{output_file}'")
            return True
        else:
            print(f"Error fetching historical data for {self.item}: {response.status_code}")
            print(response.text)
            return False

    def on_message(self, ws, message):
        try:
            response = json.loads(message)
            print("Received:", json.dumps(response, indent=4))
            
            if response.get("Resp") == "RsLogin":
                if response.get("LogonStatus") == 1:
                    print("Login successful!")
                else:
                    print("Login failed.")
                    ws.close()
                    
            elif response.get("Resp") == "RsSeckey":
                if self.data_fetched:  # Skip if we've already fetched data
                    return
                    
                keys = response.get("Keys", [])
                if keys:
                    seckey = keys[0]
                    print(f"Processing {self.item}...")
                    
                    success = self.fetch_historical_data(int(seckey))
                    
                    if success:
                        self.data_fetched = True
                        print(f"Data fetched successfully for {self.item}. Closing connection.")
                        ws.close()
                else:
                    print("No secure keys received.")
                    ws.close()
                    
            elif response.get("Resp") == "RsHeartbeat":
                ws.send(json.dumps({"Req": "RqHeartbeatAck"}))
                
            elif response.get("Resp") == "RsKickout":
                print("Received kickout message.")
                ws.close()

        except json.JSONDecodeError:
            print("Received non-JSON message:", message)

    def on_open(self, ws):
        print("WebSocket connection opened.")
        auth_key = self.get_auth_key()
        
        if not auth_key:
            print("Failed to obtain AuthKey.")
            ws.close()
            return
            
        login_data = {
            "Req": "RqLogin",
            "UserID": "",
            "AuthKey": auth_key,
            "ProductID": "",
            "Version": "1.0.0.1"
        }
        ws.send(json.dumps(login_data))

    def start(self):
        """Start fetching data"""
        ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=lambda ws, msg: self.on_message(ws, msg),
            on_open=lambda ws: self.on_open(ws),
            on_error=lambda ws, err: print(f"Error: {err}"),
            on_close=lambda ws, code, msg: print("Connection closed")
        )
        ws.run_forever()


def fetch_multiple_stocks(stock_symbols, start_date, end_date, period="D"):
    """Fetch data for multiple stocks one by one"""
    for symbol in stock_symbols:
        print(f"\nFetching data for {symbol}")
        fetcher = StockDataFetcher(
            item=symbol,
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        fetcher.start()
        time.sleep(1)  # Wait between requests

class combine_data:
    def __init__(self, stock_symbols, start_date, end_date, period):
        self.stock_symbols = stock_symbols
        self.start_date = start_date
        self.end_date = end_date
        self.period = period

    def merge(self):
        his = []
        for symbol in self.stock_symbols:
            temp = pd.read_json(f'./inputData/{symbol}_{self.start_date}_{self.end_date}_{self.period}.json')
            # os.remove(f'./inputData/{symbol}_{self.start_date}_{self.end_date}_{self.period}.json')
            temp['instrument'] = symbol
            temp['Date'] = pd.to_datetime(temp['Date'], unit='ms').dt.strftime("%Y-%m-%d")
            his.append(temp)
        fx = pd.read_csv(f'./inputData/fx.csv', index_col=0)
        his = pd.concat(his)
        his = his[['Date', 'Close', 'Volume', 'instrument']].rename(columns={'Date':'date','Close':'close','Volume':'volume'})
        his = pd.concat([his, fx])
        return his


# Example usage:
if __name__ == "__main__":
    # Set your parameters here
    stock_symbols = ["700.HK", "9988.HK", "3690.HK"]  # List of stocks
    start_date = "2023-12-01"                         # Start date
    end_date = "2024-01-11"                           # End date
    period = "D"                                      # Period (D for daily, W for weekly, M for monthly)
    
    # Fetch data for all stocks
    fetch_multiple_stocks(stock_symbols, start_date, end_date, period)
    cmd = combine_data(stock_symbols, start_date, end_date, period)
    his = cmd.merge()
    output_file = f'./inputData/hisInputData.csv'
    his.to_csv(output_file)


