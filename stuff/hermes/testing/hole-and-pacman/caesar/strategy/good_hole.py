from exchange.poloniex import Poloniex
from exchange.poloniex import PoloniexError
from utils import conf
import time
from threading import Thread
import traceback
import numpy as np

class Hole(Thread):
    """ Hole Strategy.
 
    A brief description about hole strategy.

    Attributes:
        client: Exchange client.
        pair: Pair of coins. Ex: BTC_ETH .
        buy_order: If buy order was placed or not.
        sell_order: If sell order was placed or not.
        bought: If buy order was executed or not.
        sold: If sell order was executed or not.
        buy_price: The buy price in the moment order was placed.
        sell_price: The sell price in the moment order was placed.
        desired_hole: The desired percentage of hole.
        have_hole: If have a hole or not.
        buy_id: The order number of buy.
        sell_id: The order number of sell.
        first_coin: The first coin of pair.
        second_coin: The second coin of pair.
        last_buy_order: The value of last buy order.
        last_sell_order: The value of last sell order.

    Methods:
        run: Operation starts.
        purchase_action: The actions of purchase.
        sale_action: The actions of sale.
        update: Update all values with Exchange data.
    """

    def __init__(self, client, pair, desired_hole, balance, update):
        """ Constructor of Hole class """
        Thread.__init__(self)
        self.client = client
        self.f = open("logs/hole.log","w")

        self.pair = pair
        self.first_coin = self.pair.split("_")[0]
        self.second_coin = self.pair.split("_")[1]

        self.desired_hole = desired_hole
        self.balance = balance

        self.have_hole = False

        self.last_buy_order = None
        self.last_sell_order = None

        self.buy_id = None
        self.sell_id = None
 
        self.buy_order = False
        self.sell_order = False

        self.bought = False
        self.bought_verified = False
        self.sold = False

        self.buy_price = 0.0
        self.sell_price = None

        self.end = False
        self.first_sell = True

        self.updated = update
	
	self.surf_metric = 0.0
        if update:
            self.buy_order       = True
            self.sell_order      = False
            self.bought          = True
            self.bought_verified = True
            self.sold            = False
            self.buy_price       = self.last_buy_price()
            self.sell_price      = self.check_price_to_sell()


    def last_buy_price(self):
        trade_history = self.client.returnTradeHistory(self.pair, 1507842000, 9999999999)

        for trade in trade_history:
            if trade['type'] == 'buy':
                return float(trade_history[0]['rate'])


    def run(self):
        print "(%s) - Enter in pair: %s" % (self.pair, self._time())
        self.f.write("(%s) - Enter in pair: %s" % (self.pair, self._time()))
        while not self.end:
            try:
                self.update() 
                if not self.bought:
                    self.purchase_action()
                else:
                    self.sale_action()
            except PoloniexError as e:
#               print "(%s) - Exception: %s : %s" % (self.pair, e, 
#                                                    self._time())

                self.end = True

            time.sleep(conf.check_period)

        print "(%s) - Leaving the pair: %s" % (self.pair, self._time())
        self.f.write("(%s) - Leaving the pair: %s" % (self.pair, self._time()))


    def exists_open_orders(self, pair):
        self.open_orders = self.client.returnOpenOrders(self.pair)
        return len(self.client.returnOpenOrders(self.pair)) > 0
         

    def purchase_action(self):
        """ Constructor of Hole class
           
        Description about constructor.

        Args:
            x
        Returns:
            y
        Raises:
            z
        """
        balances = self.client.returnBalances()
        self.first_balance = float(balances[self.first_coin])

        self.ticker = self.client.returnTicker()[self.pair]
        lowask_ratio = (float(self._lowest_ask()/self._highest_bid()-1.0)
                                                                   * 100)
        self.have_hole = lowask_ratio > self.desired_hole 

        if not self.buy_order:
            if self.have_hole:
                self.buy_order = True
                self.buy()
                print "(%s) - Buy order placed at %.8f : %s" % (self.pair, 
                                                           self.buy_price,
                                                             self._time())
                self.f.write("(%s) - Buy order placed at %.8f : %s" % 
                             (self.pair, self.buy_price, self._time()))
            else:
                print "(%s) - End buy order : %s" % (self.pair,
                                                  self._time())
                self.f.write("(%s) - End buy order : %s" % (self.pair,
                                                        self._time()))
                self.end = True

        else:
            self.order_book = self.client.returnOrderBook(self.pair, 2)
            self.last_buy_order = float(self.order_book['bids'][0][0])

            first_candle = self.client.returnChartData(self.pair, 900)[0]
            open_candle = float(first_candle['open'])
            close_candle = float(first_candle['close'])
            close_less_than_open = close_candle < open_candle
            
	    if not self.have_hole: #or close_less_than_open:#or not self.growth_indicator(2,5,900):
                self.buy_order = False
                self.client.cancelOrder(self.buy_id)
                print "(%s) - Existing buy order canceled : %s" % \
                                                        (self.pair,
                                                      self._time())

                self.f.write("(%s) - Existing buy order canceled : %s" % \
                                                        (self.pair,
                                                      self._time()))
                self.end = True

            elif self.buy_price < self.last_buy_order:
                self.client.cancelOrder(self.buy_id)
                self.buy()
                print "(%s) - Last buy order updated at %.8f : %s" % \
                                                           (self.pair,
                                                  self.last_buy_order,  
                                                         self._time())
                self.f.write("(%s) - Last buy order updated at %.8f : %s" % \
                                                           (self.pair,
                                                  self.last_buy_order,
                                                         self._time()))


    def buy(self):
        self.buy_price = self._highest_bid() + 0.00000001
        amount = (self.balance / self.buy_price)
  
        if amount * self.buy_price <= 0.0001:
            amount = 0.00011000 / self.buy_price
                     
        self.buy_id = str(self.client.buy(self.pair, 
                                          self.buy_price, 
                                          amount)['orderNumber'])
    

    def sale_action(self):
        """ Constructor of Hole class
           
        Description about constructor.

        Args:
            x
        Returns:
            y
        Raises:
            z
        """
        self.ticker = self.client.returnTicker()[self.pair]

       	in_sell_box = (float(self._lowest_ask()/self._highest_bid()-1.0)*100)
	box_closed  = (in_sell_box < 1.25)
        master_stop = (self.sell_price <= self.buy_price) 

	self.sold = self.was_sold()
        if self.sold:
            self.end = True
            return

        if (master_stop and not self.exist_difference(5) ):
            if not self.correct_place(0):
		if self.sell_order:
                    self.client.cancelOrder(self.sell_id)
 	        self.sell_price = self.escape_price()
	    
	        self.sell(self.sell_price)
                print "(%s) - Sell order placed to escape at %.8f : %s" % \
                                                            (self.pair, 
                                                       self.sell_price, 
                                                          self._time())
                self.f.write("(%s) - Sell order placed to escape at %.8f : %s" % \
                                                            (self.pair,
                                                       self.sell_price,
                                                          self._time()))

        else:
            stop = (self.check_price_to_sell() < self.buy_price * 1.009)
	    if self.surf() and not stop:
	        if not self.surfing():
	            if self.sell_order:
	  	        self.client.cancelOrder(self.sell_id)
		   
		    self.sell_price = self.check_price_to_surf()
		    self.sell(self.sell_price)
			
                    print "(%s) - Sell order placed to surf at %.8f : %s" % \
                                                              (self.pair, 
                                                         self.sell_price, 
								    self._time())
                    self.f.write("(%s) - Sell order placed to surf at %.8f : %s" % \
                                                              (self.pair,
                                                         self.sell_price,
                                                            self._time()))
	    else:
	        if self.sell_price != self.check_price_to_sell():
                    if self.sell_order:
                        self.client.cancelOrder(self.sell_id)
     
                    self.sell_price = self.check_price_to_sell()
                    self.sell(self.sell_price)
     
                    print "(%s) - Sell order placed at %.8f : %s" % \
                                                              (self.pair, 
                                                         self.sell_price, 
                                                            self._time())
                    self.f.write("(%s) - Sell order placed at %.8f : %s" % \
                                                              (self.pair,
                                                         self.sell_price,
                                                            self._time()))
		else:
            	    print "(%s) Sell order correct at %.8f " % (self.pair,
		    					  self.sell_price)
    def escape_price(self):
        number_of_orders = 5
        self.order_book = self.client.returnOrderBook(self.pair, 
                                                      number_of_orders)
        sell_orders = self.order_book['asks']
        value_orders = []

        for order in sell_orders:
            value_orders.append(float(order[0]))
	
        price_to_sell = value_orders[0] - 0.000000005
        return price_to_sell

    def surf(self):
	number_of_orders = 5
	self.order_book = self.client.returnOrderBook(self.pair,number_of_orders)
	sell_orders = self.order_book['asks']
	buy_orders  = self.order_book['bids'] 

	value_orders_sell = []
	value_orders_buy  = []

	for order in buy_orders:
            value_orders_buy.append(float(order[0])) 	

	if self.growth_indicator(17,72,900) :
	    return True
	else:
	    return False

    def growth_indicator(self,top,bottom,period):
	timestamp = time.time()
	timestamp_range = timestamp - (period * 144)
	chart_data = self.client.returnChartData(self.pair, period,timestamp_range, timestamp)
	
	EMA_bottom = self.ema(chart_data,bottom)
	EMA_top = self.ema(chart_data,top)
	
	if EMA_top >= EMA_bottom :
	    return True
        else:
	    return False


    def surfing(self):
	number_of_orders = 5
        self.order_book = self.client.returnOrderBook(self.pair, 
                                                      number_of_orders)
	sell_orders = self.order_book['asks']
	value_orders = []

        for order in sell_orders:
            value_orders.append(float(order[0]))

        if self.sell_price == self.check_price_to_surf():
	    print "(%s) - Surfing at %.8f" % (self.pair,self.sell_price)
            return True
	
	print "(%s) - Not surfing" % self.pair
	return False

    def correct_place(self,place):
        number_of_orders = 5
	self.order_book = self.client.returnOrderBook(self.pair, 
                                                      number_of_orders)
        sell_orders = self.order_book['asks']
        value_orders = []

        for order in sell_orders:
            value_orders.append(float(order[0]))

        if value_orders[place] == self.sell_price:
            print "(%s) Sell order correct at %.8f " % (self.pair,
							self.sell_price)
            return True
	     
    def exist_difference(self,number_of_orders):
        self.order_book = self.client.returnOrderBook(self.pair, 
                                                      number_of_orders)
        sell_orders = self.order_book['asks']
        value_orders = []

        for order in sell_orders:
            value_orders.append(float(order[0]))

        for i in range(number_of_orders - 1):
            if value_orders[i + 1] - value_orders[i] > 0.00000050:
                print "(%s) Exist difference" % self.pair
		if value_orders[i+1] > self.buy_price:
                    return True
     
    def check_price_to_buy(self):
        number_of_orders = 4
        self.order_book = self.client.returnOrderBook(self.pair, 
                                                      number_of_orders)
        buy_orders = self.order_book['bids']
        value_orders = []

        for order in buy_orders:
            value_orders.append(float(order[0]))

        price_to_buy = value_orders[0]

        for i in range(number_of_orders - 1):
            if value_orders[i + 1] - value_orders[i] > 0.00000100:
                price_to_buy = value_orders[i+1] + 0.00000001

        return price_to_buy


    def check_price_to_sell(self):
        number_of_orders = 5
        self.order_book = self.client.returnOrderBook(self.pair, 
                                                      number_of_orders)
        sell_orders = self.order_book['asks']
        value_orders = []
	limit = self.buy_price * 1.01

        for order in sell_orders:
            value_orders.append(float(order[0]))
	
        price_to_sell = value_orders[0]  #Tamo junto
	if ( value_orders[0] < limit ):
            for i in reversed(range(number_of_orders - 1)):
                if value_orders[i + 1] - value_orders[i] > 0.00000050:
                    price_to_sell = value_orders[i + 1]

        return price_to_sell

    def check_price_to_surf(self):
	
        price_to_surf = self.buy_price * 1.015
	
        return price_to_surf
    
    def candle_size(self,candle): 
        open_candle = float(candle['open'])
        close_candle = float(candle['close'])
	
	return ((close_candle / open_candle)-1.0) * 100
    
    def candle_gigante(self,candle):
        first_candle = self.candle_size(candle[0])
        second_candle = self.candle_size(candle[1])

        if (first_candle > 0) and (second_candle < 0) \
	    and (first_candle > (2 * abs(second_candle) )):
		return True       
    
    def candle_hammer(self,candle):
        first_candle = self.candle_size(candle[0])
        second_candle = self.candle_size(candle[1])
	
	open_candle = float(candle[0]['open'])
	head = float(candle[0]['high'])
	tail = float(candle[0]['low'])

        if (first_candle > 0) and (second_candle < 0) \
	    and (open_candle > tail*1.4):
		return True       

    def sma(self,chart_data, period):
        average = 0.0
        for i in range(period):
            average = average + float(chart_data[len(chart_data)-1-i]['close'])
    
        return average / float(period)
    
    def ema(self,chart_data, period):
        chart_data_organized = []
	for k in range(1,len(chart_data)):
            chart_data_organized.append(chart_data[k-1]['close'])
        
        alpha = 2/(period +1.0)
        alpha_rev = 1-alpha
        chart_data_fl = np.array(chart_data_organized,dtype=float)
        n = chart_data_fl.shape[0]
    
        pows = alpha_rev**(np.arange(n+1))
    
        scale_arr = 1/pows[:-1]
        offset = chart_data_fl[0]*pows[1:]
        pw0 = alpha*alpha_rev**(n-1)
    
        mult = chart_data_fl*pw0*scale_arr
        cumsums = mult.cumsum()
        out = offset + cumsums*scale_arr[::-1]
        out_float = float(out[-1])
        return out_float


    def sell(self, sell_price):
        balances = self.client.returnBalances()
        self.second_balance = float(balances[self.second_coin])
        self.sell_price = sell_price 
        self.sell_id = str(self.client.sell(self.pair,
                                            self.sell_price, 
                                            self.second_balance)
                                            ['orderNumber'])
        self.sell_order = True


    def update(self):
        """ Constructor of Hole class
           
        Description about constructor.

        Args:
            x
        Returns:
            y
        Raises:
            z
        """
        self.trade_history = self.client.returnTradeHistory(self.pair)
        self.bought = self.was_bought()


    def was_bought(self):
        if not self.buy_order:
            return False

        if self.bought_verified:
            return True

        for history in self.trade_history:
            if history['orderNumber'] == self.buy_id \
            and not self.bought_verified:
                print "(%s) - Buy order executed : %s" % (self.pair, 
                                                      self._time())
                self.f.write("(%s) - Buy order executed : %s" % (self.pair,
                                                      self._time()))

                self.bought_verified = True

                return True

        return False


    def was_sold(self):
        if not self.sell_order:
            return False

        for history in self.trade_history:
            if history['orderNumber'] == self.sell_id:
                print "(%s) - Sell order executed : %s" % (self.pair, 
                                                       self._time())
                self.f.write("(%s) - Sell order executed : %s" % (self.pair,
                                                       self._time()))
                return True

        return False


    def _lowest_ask(self):
        return float(self.ticker['lowestAsk'])


    def _highest_bid(self):
        return float(self.ticker['highestBid'])


    def _time(self):
        return time.asctime(time.localtime(time.time()))
