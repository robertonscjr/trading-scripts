import numpy as np
import math

def last(ticker, pair):
    last = float(ticker[pair]['last'])

    return last

def highest_bid(ticker, pair):
    highest_bid = float(ticker[pair]['highestBid'])

    return highest_bid

def lowest_ask(ticker, pair):
    lowest_ask = float(ticker[pair]['lowestAsk'])

    return lowest_ask 

def get_balance(balances, coin):
    balance = float(balances[coin])

    return balance

def get_ticker(client):
    return client.returnTicker()

def get_order_book(client):
    return client.returnOrderBook('all', 1)

def get_open_orders(client):
    return client.returnOpenOrders('all')

def get_balances(client):
    return client.returnBalances()

def update_minimums(ticker, client):
    minimum = {}

    for pair in ticker:
        candlestick = client.returnChartData(pair, 300)
        candle = candlestick[len(candlestick)-1]
        minimum[pair] = float(candle['open'])

    return minimum

def cancel_orders(client, orders):
    for order in orders:
        client.cancelOrder(order['orderNumber'])

def candle_info(client, pair):
    candlestick = client.returnChartData(pair, 1800)
    candle = candlestick[len(candlestick)-1]
    candle_open = float(candle['open'])
    candle_close = float(candle['close'])

    return candle_open, candle_close

def get_first_order_amount(order_book, pair, order_type):
    return order_book[pair][order_type][0][1]

def get_first_order_price(order_book, pair, order_type):
    return float(order_book[pair][order_type][0][0])

def sma(chart_data, period):
    average = 0.0
    for i in range(period):
        average = average + float(chart_data[len(chart_data)-1-i]['close'])

    return average / float(period)

def bollinger(chart_data, period):
    top = 0.0
    bot = 0.0
    mid = sma(chart_data, period)

    closes = []
    for i in range(len(chart_data)):
        closes.append(float(chart_data[len(chart_data)-1-i]['close']))

    std_sum = 0.0
    for i in range(period):
        std_sma = sma(chart_data[len(chart_data)-i-period:len(chart_data)-i], period)
        std_sum += (closes[i] - std_sma) ** 2

    std_avg = std_sum / period
    std = math.sqrt(std_avg)

    top = mid + 2 * std
    bot = mid - 2 * std 

    return top, mid, bot

def ema(chart_data, period):
    ema = float(chart_data[len(chart_data) - int(period)]['close'])
#   ema = sma(chart_data, period)

    k = 2.0/(float(period) + 1.0)
    for i in range(1, period):
        ema = ema * (1-k) + float(chart_data[len(chart_data)-period+i]['close']) * k

    return ema
    
#   chart_data_organized = []
#   for k in range(1,len(chart_data)):
#       chart_data_organized.append(chart_data[k-1]['close'])
#   
#   alpha = 2/(period +1.0)
#   alpha_rev = 1-alpha
#   chart_data_fl = np.array(chart_data_organized,dtype=float)
#   n = chart_data_fl.shape[0]
#
#   pows = alpha_rev**(np.arange(n+1))
#
#   scale_arr = 1/pows[:-1]
#   offset = chart_data_fl[0]*pows[1:]
#   pw0 = alpha*alpha_rev**(n-1)
#
#   mult = chart_data_fl*pw0*scale_arr
#   cumsums = mult.cumsum()
#   out = offset + cumsums*scale_arr[::-1]
#   out_float = float(out[-1])
#   return out_float
