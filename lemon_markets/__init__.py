# pylama:ignore=E501,C901
'''lemon_markets, a wrapper for various lemon.markets enpoints

Attributes:
    debug (bool): Whether to print debug messages. Default is False
    request_timeout (float): The timeout when making requests. Default is 10.0
    request_retries (int): how many times to retry a request. Default is 5'''

from json import loads
from multiprocessing import freeze_support, Process
from time import ctime, time

from websocket import create_connection
from urllib3 import PoolManager


debug = False
request_timeout = 10.0
request_retries = 5


class WebSocket():
    '''Gives acess to the websocket server at lemon.markets

    Args:
        callback (function, required): Function to call when websocket data is received. It should have 2 arguments:
            instrument (Instrument): the Instrument for which data was received and
            trade (Trade): the Trade that contains time and price
        timeout (int, optional): The timeout in seconds after which the websocket will reconnect. Default is 10
        frequency_limit (int, optional): The maximum frequency in seconds at which the callback should be called. Default is 0 (no limit)

    Note:
        Leave out the parentheses when passing your callback function!

    Attributes:
        timeout (float): The timout after which to reconnect
        callback (function): The function to call when data is received
        subscribed (list (Instrument)): A list containing all Instruments subscribed to
    '''

    def __init__(self, callback=None,
                 timeout=10,
                 frequency_limit=0):

        assert None not in [callback, frequency_limit, timeout], 'callback must be specified'

        self._last_message_time = 0
        self._frequency_limit = frequency_limit
        self.timeout = timeout
        self.callback = callback
        self.subscribed = []

        if debug:
            print(f'[{ctime()}:DEBUG] Initialised WebSocket class')

    def __str__(self):

        return f'Websocket connection to api.lemon.markets. Currently subscribed symbols: {self._subscribed}'

    def __repr__(self):

        return f'Websocket connection to api.lemon.markets. Currently subscribed symbols: {self._subscribed}'

    def __del__(self):

        try:
            if self._ws_process.is_alive():
                self._ws_process.terminate()
                if debug:
                    print(f'[{ctime()}:DEBUG] Stopped worker because class reference was deleted')
        except Exception:
            pass

    def _ws_worker(self):

        if debug:
            print(f'[{ctime()}:DEBUG] Opened websocket connection')
        while True:
            ws = create_connection('ws://api.lemon.markets/streams/v1/marketdata', timeout=self.timeout)
            for each in self.subscribed:
                ws.send('{"action": "subscribe", "type": "trades", "specifier": "with-uncovered", "value": "%s"}' % (each.isin))
            while True:
                try:
                    response = eval(ws.recv())
                    if(time() - self._last_message_time > self._frequency_limit):
                        try:
                            self.callback(Instrument(response['isin']), Trade(response['price'], response['date']))
                        except Exception as e:
                            raise ValueError(f'[{ctime()}:ERROR] Error in callback function at {self.callback}: {e}')
                        self._last_message_time = time()
                except Exception:
                    break
            ws.close()
            if debug:
                print(f'[{ctime()}:DEBUG] Reopening websocket connection (caused by timeout ({self._timeout})',
                      'or serverside disconnect)')

    def subscribe(self, instrument=None):
        '''Subscribe to realtime data from the given instrument

        Args:
            instrument (Instrument, required): The Instrument you want to subscribe to

        Note:
            The Instrument can be obtained through calling :meth:`lemon_markets.REST.list_instruments`
        '''

        assert instrument is not None, 'instrument must be specified'
        if instrument in self.subscribed:
            return
        self.subscribed.append(instrument)

        if debug:
            debug_str = f"Subscribed to data from '{instrument.title}'. "

        if len(self.subscribed) == 1:
            self._ws_process = Process(target=self._ws_worker)
            self._ws_process.start()
            if debug:
                debug_str += 'Started worker'

        if debug:
            print(f'[{ctime()}:DEBUG] {debug_str}')

    def unsubscribe(self, instrument=None):
        '''Unsubscribe from realtime data for the given instrument

        Args:
            instrument (Instrument, required): The Instrument you want to unsubscribe from
        '''

        assert instrument is not None, 'instrument must be specified'

        try:
            self.subscribed.remove(instrument)
        except ValueError:
            pass

        if debug:
            debug_str = f"Unsubscribed from data for '{instrument.title}'. "

        if len(self.subscribed) == 0:
            self._ws_process.terminate()
            if debug:
                debug_str += 'Stopped worker (no websockets active)'

        print(f'[{ctime()}:DEBUG] {debug_str}')


class Account():
    '''Gives you acess to account data from lemon.markets

    Args:
        account_uuid (str, required): The UUID of the account
        token (str, required): The token used to authenticate with the account

    Note:
        You are most likely to never use this, since a list of all Accounts for
        a token can be obtained by calling :func:`lemon_markets.get_accounts`

    Attributes:
        uuid (str): The account uuid
        token (str): The token used to authenticate requests
        name (str): Human-readable name of the account
        type (str): Currently only 'demo'
        currency (str): The currency of your account, e.g. 'USD', 'EUR', ...

    Note:
        You are not able to set attributes for this class
    '''

    def __init__(self, account_uuid=None, token=None):

        assert None not in [account_uuid, token], 'account_uuid and token must be specified. debug_flag cannot be None'

        self.__dict__['uuid'] = account_uuid
        self.__dict__['token'] = token
        self.__dict__['_auth_header'] = {'Authorization': f'Token {self.token}'}
        r_userdata = _request(method='GET',
                              url=f'https://api.lemon.markets/rest/v1/accounts/{self.uuid}/',
                              headers=self._auth_header)
        self.__dict__['name'] = r_userdata['name']
        self.__dict__['type'] = r_userdata['type']
        self.__dict__['currency'] = r_userdata['currency']

    def __str__(self):

        return f'account at lemon.markets,'\
            f'uuid: {self.uuid},'\
            f'token: {self.token},'\
            f'name: {self.name},'\
            f'type: {self.type},'\
            f'currency: {self.currency}'

    def __repr__(self):

        return f'account at lemon.markets,'\
            f'uuid: {self.uuid},'\
            f'token: {self.token},'\
            f'name: {self.name},'\
            f'type: {self.type},'\
            f'currency: {self.currency}'

    def __getattr__(self,
                    name):

        if name not in ['name', 'type', 'currency']:
            raise AttributeError(f"'Order' object has no attribute '{name}''")

        r_userdata = _request(method='GET',
                              url=f'https://api.lemon.markets/rest/v1/accounts/{self.uuid}/',
                              headers=self._auth_header)
        self.__dict__['name'] = r_userdata['name']
        self.__dict__['type'] = r_userdata['type']
        self.__dict__['currency'] = r_userdata['currency']

        return self.__dict__[name]

    def __setattr__(self, name, value):
        if debug:
            print(f"[{ctime()}:DEBUG] The attributes of 'Account' object cannot be set directly. Nothing has been changed")

    def create_order(self,
                     side=None,
                     instrument=None,
                     quantity=None,
                     order_type=None,
                     valid_until=None,
                     limit_price=None,
                     stop_price=None):

        '''Create an order

        Args:
           side (str, required): Either 'buy' or 'sell. It's quite obvious
           instrument (Instrument, required): The Instrument you want to create an order for
           quantity (int, required): The amount you want to buy or sell
           order_type (str, required): Either 'market', 'stop_market', 'limit' or 'stop_limit'
           valid_until (float, optional): The unix timestamp you want the order to be valid until
           limit_price (float, required if order_type is 'limit' or 'stop_limit'): The order will be placed at <limit_price> or better
           stop_price (float, required if order_type is 'stop' or 'stop_limit'): The price the order will be placed at

        Returns:
            Order: The Order object representing the order

        Note:
            The order can also be obtained by calling :meth:`lemon_markets.Account.list_orders`.
            Also the instrument is returned when calling :meth:`lemon_markets.REST.list_instruments`
        '''

        if valid_until is None:
            valid_until = time()

        assert None not in [side, instrument, quantity, valid_until, order_type], \
            'side, instrument and quantity have to be specified. valid_until cannot be None'
        assert order_type in ['limit', 'stop_limit', 'market', 'stop_market'], \
            'Unsupported order type!'
        if limit_price is None and 'limit' in order_type:
            raise AssertionError(f'Limit price has to be specified for orders of type {order_type}')
        if stop_price is None and 'stop' in order_type:
            raise AssertionError(f'Stop price has to be specified for orders of type {order_type}')

        r_order = _request(method='POST',
                           url=f'https://api.lemon.markets/rest/v1/accounts/{self.uuid}/orders/',
                           headers=self._auth_header,
                           fields={
                               'instrument': instrument.isin,
                               'side': side,
                               'quantity': quantity,
                               'valid_until': valid_until,
                               'type': order_type,
                               'limit_price': limit_price,
                               'stop_price': stop_price
                           })

        if debug:
            print(f'[{ctime()}:DEBUG] Created order (side: {side}, instrument: {instrument}, quantity: {quantity}, ',
                  f'valid_until: {valid_until}), order_type: {order_type}, limit_price: {limit_price}, stop_price: {stop_price}')
        return Order(r_order['uuid'], self.account, self.token)

    def delete_order(self,
                     order=None):
        '''Delete the specified order

        Args:
            order (Order, required): The Order object of the order

        Returns:
            bool: True if successful, otherwise False
        '''

        assert order is not None, 'order must be specified'

        _request(method='DELETE',
                 url=f'https://api.lemon.markets/rest/v1/accounts/{self.uuid}/orders/{order.id}/',
                 headers={
                     'Authorization': f'Token {self.token}'
                 })

        orderlist = self.list_orders(99999, 0)
        for item in orderlist:
            if item.id == order.id and item.status != 'deleted':
                if debug:
                    print(f'[{ctime()}:DEBUG] Order could not be deleted')
                    return False
        if debug:
            print(f'[{ctime()}:DEBUG] Order successfully deleted')
        return True

    def list_orders(self,
                    limit=200,
                    offset=0,
                    side=None,
                    order_type=None,
                    status=None,
                    created_at_until=None,
                    created_at_from=None):
        '''List orders in your account

        Args:
            limit (int, optional): How many results to return at most
            offset (int, optional): The <offset> first results are skipped
            side (str, optional): Filter for orders of side 'buy' or 'sell'
            order_type (str, optional): The type of orders you want to filter for, e.g. 'limit', 'stop_limit', 'market' or 'stop_market'
            status (string, optional): Filter for order status 'executed', 'open', 'deleted', 'in_process' or 'expired'
            created_at_until (float, optional): The unix timestamp before which the orders you want to filter for were created
            created_at_from (float, optional): The unix timestamp after which the orders you want to filter for were created

        Returns:
            list (Order): A list containing all orders and information about them
        '''

        assert None not in [limit, offset], 'limit and offset cannot be None'

        r_orderlist = _request(method='GET',
                               url=f'https://api.lemon.markets/rest/v1/accounts/{self.uuid}/orders/',
                               headers=self._auth_header,
                               fields={
                                   'limit': limit,
                                   'offset': offset,
                                   'side': side,
                                   'execution_type': order_type,
                                   'status': status,
                                   'created_at_until': created_at_until,
                                   'created_at_from': created_at_from
                               })
        returnlist = [] * r_orderlist['count']
        for i, result in enumerate(r_orderlist['results']):
            limit_price = stop_price = None
            if 'limit_price' in result:
                limit_price = result['limit_price']
            if 'stop_price' in result:
                stop_price = result['stop_price']
            returnlist[i] = Order(result['uuid'],
                                  self.account,
                                  self.token,
                                  result['quantity'],
                                  limit_price,
                                  stop_price,
                                  result['type'],
                                  result['side'],
                                  Instrument(result['instrument']['isin']),
                                  result['created_at'],
                                  result['processed_at'],
                                  result['processed_quantity'],
                                  result['average_price'],
                                  result['valid_until'])

        return returnlist

    def list_transactions(self,
                          limit=200,
                          offset=0,
                          date_from=None,
                          date_until=None):
        '''List transactions in your account

        Args:
            limit (int, optional): The maximum number of results to return. Default is 200
            offset (int, optional): How many of the first results to skip
            date_from (float, optional): the unix time after which the filtered transactions were made
            date_until (float, optional): the unix timestamp before which the filtered transactions were made

        Returns:
            list (Transaction): A list of transactions and their information
        '''

        assert None not in [limit, offset], 'limit and offset cannot be None'

        r_transactlist = _request(method='GET',
                                  url=f'https://api.lemon.markets/rest/v1/accounts/{self.uuid}/transactions/',
                                  headers=self._auth_header,
                                  fields={
                                      'limit': limit,
                                      'offset': offset,
                                      'date_until': date_until,
                                      'date_from': date_from
                                  })
        returnlist = [] * len(r_transactlist['results'])
        for i, result in enumerate(r_transactlist['results']):
            returnlist[i] = Transaction(result['uuid'],
                                        self,
                                        result['name'],
                                        result['amount'],
                                        result['related_order']['volume'],
                                        Instrument(result['related_order']['instrument']),
                                        result['time'])
        return returnlist

    def get_portfolio(self):
        '''Get the Portfolio object representing the account's portfolio

        Returns:
            Portfolio: The Portfolio object representing the account's portfolio'
        '''

        return Portfolio(self)

    def get_trades_intraday(self,
                            instrument=None,
                            order=None,
                            date_from=None,
                            date_until=None,
                            limit=1000,
                            offset=0):
        '''Get a list of trades for a specific instrument for today

        Args:
            instrument (Instrument, required): The Instrument to get data from
            order (str, optional): The ordering of your data. Either 'date' or '-date',
                depending on if you want to get newest or oldest first. Default is unordered
            date_from (float, optional): The unix timestamp after which all trades listed should have happened
            date_to (float, optional): The unix timestamp before which all trades listed should have happened
            limit (int, optional): The maximum number of trades to return. Default in 1000
            offset (int, optional): How many of the first results to skip

        Returns:
            list (Trade): A list containing all trades with price and unix time
        '''

        assert instrument is not None, 'instrument must be specified'
        assert order is None or order in ['date', '-date']

        r_tradeslist = _request(method='GET',
                                url=f'https://api.lemon.markets/rest/v1/data/instruments/{instrument.isin}/ticks/',
                                headers=self._auth_header,
                                fields={
                                    'ordering': order,
                                    'date_from': date_from,
                                    'date_until': date_until,
                                    'limit': limit,
                                    'offset': offset
                                })
        returnlist = [] * len(r_tradeslist['results'])
        for i, result in enumerate(r_tradeslist['results']):
            returnlist[i] = Trade(result['price'], result['date'])
        return returnlist

    def get_latest_trade(self,
                         instrument=None):
        '''Returns info on the latest trade for the specified symbol

        Args:
            instrument (Instrument, required): The Instrument you want to get the latest trade from

        Returns:
            Trade: A Trade object containing the price and timestamp of the latest trade
        '''

        assert instrument is not None, 'instrument must be specified'

        r_latesttrade = _request(method='GET',
                                 url=f'https://api.lemon.markets/rest/v1/data/instruments/{instrument.isin}/ticks/latest/',
                                 headers=self._auth_header)
        return Trade(r_latesttrade['price'], r_latesttrade['date'])


class REST():
    '''Gives acess to very basic REST calls'''

    def __str__(self):
        return 'REST object'

    def __repr__(self):
        return 'REST object'

    def list_instruments(self,
                         search=None,
                         instrument_type=None,
                         limit=1000,
                         offset=0):
        '''Get a list of all available instruments

        Args:
            search (str, optional): Search for isin, wkn or title
            instrument_type (str, optional): Either 'stocks', 'bonds' or 'fonds'
            limit (int, optional): Maximum number of instruments to return. Default is 1000
            offset (int, optional): Number of first results to skip

        Returns:
            list (Instrument): A list containing all instruments and information about them
        '''

        assert None not in [limit, offset], 'limit and offset cannot be None'

        page_list = []
        while limit > 0:
            if limit >= 1000:
                page_list.append(1000)
                limit -= 1000
            else:
                page_list.append(limit)
                limit = 0

        instrument_list = []
        for i, item in enumerate(page_list):
            page_offset = i * 1000 + offset
            r_instrumentlist = _request(method='GET',
                                        url='https://api.lemon.markets/rest/v1/data/instruments/',
                                        fields={
                                            'search': search,
                                            'type': instrument_type,
                                            'limit': item,
                                            'offset': page_offset
                                        })
            instrument_list += r_instrumentlist['results']
            if r_instrumentlist['next'] == 'null':
                break
        returnlist = [] * len(instrument_list)
        for i, result in enumerate(instrument_list):
            returnlist[i] = Instrument(result['isin'],
                                       result['wkn'],
                                       result['title'],
                                       result['type'],
                                       result['symbol'])
        return instrument_list

    def get_m1_candlesticks(self,
                            instrument=None,
                            ordering=None,
                            date_from=None,
                            date_until=None,
                            limit=1000,
                            offset=0):
        '''Get a list of 1-minute-granularity candles for today

        Args:
            instrument (Instrument, required): The Instrument to get data for
            ordering (str, optional): Either 'date' or '-date' depending on if you want to get newest or oldest first. Default is unordered
            date_from (float, optional): The unix timestamp after which all candles listed should have been recorded
            date_to (float, optional): The unix timestamp before which all candles listed should have been recorded
            limit (int, optional): The maximum number of candles to return. Default in 1000
            offset (int, optional): How many of the first results to skip

        Returns:
            list (Candle): A list containing the candles and information about them
        '''

        assert None not in [instrument, limit, offset], 'instrument must be specified'
        assert ordering is None or ordering in ['date', '-date'], "ordering must be None, 'date' or '-date'"

        pages_list = []
        while limit > 0:
            if limit >= 1000:
                pages_list.append(1000)
                limit -= 1000
            else:
                pages_list.append(limit)
                limit = 0

        m1candles_list = []
        for i, item in enumerate(pages_list):
            page_offset = i * 1000 + offset
            r_m1candles = _request(method='GET',
                                   url=f'https://api.lemon.markets/rest/v1/data/instruments/{instrument.isin}/candle/m1/',
                                   fields={
                                       'ordering': ordering,
                                       'date_from': date_from,
                                       'date_until': date_until,
                                       'limit': item,
                                       'offset': page_offset
                                   })
            m1candles_list += r_m1candles['results']
            if r_m1candles['next'] == 'null':
                break
        returnlist = [] * len(m1candles_list)
        if ordering == '-date':
            for i, result in enumerate(m1candles_list):
                returnlist[-i] = Candle(result['open'], result['high'], result['low'], result['close'], 60, result['date'])
        else:
            for i, result in enumerate(m1candles_list):
                returnlist[i] = Candle(result['open'], result['high'], result['low'], result['close'], 60, result['date'])
        return returnlist

    def get_m1_candlestick_latest(self,
                                  instrument=None):
        '''Get the latest m1-candlestick

        Args:
            instrument (Instrument, required): The Instrument you want to get the latest candle from

        Returns:
            Candle: A Candle object containing information about the latest candle
        '''

        assert instrument is not None, 'instrument must be specified'

        r_latestcandle = _request(method='GET',
                                  url=f'https://api.lemon.markets/rest/v1/data/instruments/{instrument.isin}/candle/m1/latest/')
        return Candle(r_latestcandle['open'],
                      r_latestcandle['high'],
                      r_latestcandle['low'],
                      r_latestcandle['close'],
                      60,
                      r_latestcandle['date'])


class Candle():
    '''A primitive class representing a candle

    You will never use this class directly, it is the return of some functions

    Args:
        open (int, required): The open price
        high (int, required): The high price
        low (int, required): The low price
        close (int, required): The close price
        width (int, required): The time in seconds the candle represents (in your graph horizontally)
        time (float, required): The unix time stamp the candle was created at

    Attributes:
        open (int): The open price
        high (int): The high price
        low (int): The low price
        close (int): The close price
        width (int): The time in seconds the candle represents (in your graph horizontally)
        time (float): The unix time stamp the candle was created at

    Further information on the time argument and attribute is needed
    '''

    def __init__(self, open=None, high=None, low=None, close=None, width=None, time=None):

        assert None not in [open, high, low, close, width, time], 'all arguments must be specified'

        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.width = width
        self.time = time

    def __repr__(self):
        return f'Candle object: open: {self.open}, high: {self.high},'\
            f' low: {self.low}, close: {self.close}, width: {self.width}, time: {self.time}'

    def __str__(self):
        return f'Candle object: open: {self.open}, high: {self.high},'\
            f' low: {self.low}, close: {self.close}, width: {self.width}, time: {self.time}'


class Instrument():
    '''Class representing an instrument

    Args:
        isin (str, required): The isin of the instrument

    Note:
        Do not specify more properties than just isin. The instrument's properties will automatically be set

    Attributes:
        isin (str): The isin of the instrument
        wkn (str): The instrument's wkn
        title (str): A sanity-friendly description of the instrument
        type (str): The type of the instrument. Possible values are 'stocks', 'bonds', ... (more information needed)
        symbol (str): The symbol representing the instrument. For tesla this is 'TSLA'

    Note:
        You can only change the isin attribute, which will also update all other attributes
    '''

    def __init__(self,
                 isin=None,
                 wkn=None,
                 title=None,
                 type=None,
                 symbol=None):

        assert isin is not None, 'Isin must be specified'

        self.__dict__['isin'] = isin

        if None not in [wkn, title, type, symbol]:
            self.__dict__['wkn'] = wkn
            self.__dict__['title'] = title
            self.__dict__['type'] = type
            self.__dict__['symbol'] = symbol

    def __getattr__(self,
                    name):

        if name not in ['wkn', 'title', 'type', 'symbol']:
            raise AttributeError(f"'Instrument' object has no attribute '{name}''")

        instrumentinfo = _request(method='GET',
                                  url=f'https://api.lemon.markets/rest/v1/data/instruments/{self.isin}/')
        self.__dict__['wkn'] = instrumentinfo['wkn']
        self.__dict__['title'] = instrumentinfo['title']
        self.__dict__['type'] = instrumentinfo['type']
        self.__dict__['symbol'] = instrumentinfo['symbol']

        return self.__dict__[name]

    def __setattr__(self,
                    key,
                    value):
        if key == 'isin':
            self.__dict__.clear()
            self.__dict__['isin'] = value
            return
        if debug:
            print(f"[{ctime()}:DEBUG] The attributes aside from 'isin' of 'Instrument' object cannot be set directly. Nothing has been changed")

    def __str__(self):

        return f'Instrument object, isin: {self.isin}, title: {self.title},'\
            f' wkn: {self.wkn}, type: {self.type}, symbol: {self.symbol}'

    def __repr__(self):

        return f'Instrument object, isin: {self.isin}, title: {self.title},'\
            f' wkn: {self.wkn}, type: {self.type}, symbol: {self.symbol}'


class Transaction():
    '''Class representing a transaction

    You will never directly use this class, it is the return of some functions

    Args:
        id (str, required): The id of the transaction
        account (Account, required): The account

    Note:
        Do not specify more properties than isin and account. The transactions's properties will automatically be set

    Attributes:
        id (str): The id of the order
        account (Account): The account
        name (str): A human-readable name for the transaction
        amount (float): The amount of money in your currency that was moved
        order_volume (float): The volume of the order in your currency
        instrument (Instrument): The Instrument related to this order
        time (float): The unix time when the transaction was executed

    Note:
        You can not change any of the attributes
    '''

    def __init__(self,
                 id=None,
                 account=None,
                 name=None,
                 amount=None,
                 order_volume=None,
                 instrument=None,
                 time=None):

        assert None not in [id, account], 'Id, account and token must be specified'

        self.__dict__['id'] = id
        self.__dict__['account'] = account

        if None not in [name, amount, order_volume, instrument, time]:
            self.__dict__['name'] = name
            self.__dict__['amount'] = amount
            self.__dict__['order_volume'] = order_volume
            self.__dict__['instrument'] = instrument
            self.__dict__['time'] = time

    def __getattr__(self,
                    name):

        if name not in ['name', 'amount', 'order_volume', 'order_isin', 'time']:
            raise AttributeError(f"'Transaction' object has no attribute '{name}''")

        transactioninfo = _request(method='GET',
                                   url=f'https://api.lemon.markets/rest/v1/accounts/{self.account.isin}/transactions/{self.id}/',
                                   headers='{"Authorization": "Token %s"}' % self.account.token)
        self.__dict__['name'] = transactioninfo['name']
        self.__dict__['amount'] = transactioninfo['amount']
        self.__dict__['order_volume'] = transactioninfo['related_order']['volume']
        self.__dict__['instrument'] = Instrument(transactioninfo['related_order']['instrument'])
        self.__dict__['time'] = transactioninfo['time']

        return self.__dict__[name]

    def __setattr__(self, key, value):
        if debug:
            print(f"[{ctime()}:DEBUG] The attributes of 'Transaction' object cannot be set directly. Nothing has been changed")

    def __str__(self):

        return f'Transaction object, id: {self.id}, time: {self.time}, account: {str(self.account)}, name: {self.name},'\
            ' amount: {self.amount}, order_volume: {self.order_volume}, order_isin: {self.order_isin}'

    def __repr__(self):

        return f'Transaction object, id: {self.id}, time: {self.time}, account: {str(self.account)}, name: {self.name},'\
            f' amount: {self.amount}, order_volume: {self.order_volume}, order_isin: {self.order_isin}'


class Trade():
    '''A primitive class representing a trade

    You will never use this class directly, it is the return of some functions

    Args:
        price (float): The price
        time (float): The unix timestamp

    Attributes:
        price (float): The price
        time (float): The unix time
    '''

    def __init__(self,
                 price=None,
                 time=None):

        assert None not in [price, time], 'Price and time must be specified'

        self.price = price
        self.time = time

    def __str__(self):
        return f'Trade object, price: {self.price}, time: {self.time}'

    def __repr__(self):
        return f'Trade object, price: {self.price}, time: {self.time}'


class Order():
    '''Also a very (it's ironic) simple class for holding orders

    You will never directly use this class, it is the return of some functions

    Args:
        id (str, required): The id of the transaction
        account (Account, required): The account

    Note:
        Do not specify more properties than isin and account. The order's properties will automatically be set

    Attributes:
        id (str): The id of the order
        account (Account): The account
        quantity (int): The quantity of the instrument
        limit_price (float): The limit price of the order. None if type is 'market' or 'stop_market'
        stop_price (float): The stop price of the order. None if type is 'market' or 'limit'
        type (string): The type of the order. Either 'market', 'stop_market', 'limit' or 'stop_limit'
        side (string): The side of the order. Either 'buy' or 'sell'
        instrument (Instrument): The Instrument object representing the instrument
        created_at (float): The time the order was created at
        processed_at (float): the time the (first part of the) order was executed (more information needed)
        processed_quantity (int): The quantity of the order that was executed (this is due to 'partial execution',
            means that the order is executed in 'parts')
        avg_price (float): The weighted average price of all executed partial orders
        valid_until (float): Time untul which the order is valid.

    Note:
        You can not change any of the attributes
    '''

    def __init__(self,
                 id=None,
                 account=None,
                 quantity=None,
                 limit_price=None,
                 stop_price=None,
                 type=None,
                 side=None,
                 instrument=None,
                 created_at=None,
                 processed_at=None,
                 processed_quantity=None,
                 avg_price=None,
                 valid_until=None):

        assert None not in [id, account], 'Id, account and token must be specified'

        self.__dict__['id'] = id
        self.__dict__['account'] = account

        if None not in [quantity, type, side, instrument,
                        created_at, processed_at, processed_quantity, avg_price, valid_until]:

            self.__dict__['quantity'] = quantity
            self.__dict__['limit_price'] = limit_price
            self.__dict__['stop_price'] = stop_price
            self.__dict__['type'] = type
            self.__dict__['side'] = side
            self.__dict__['instrument'] = instrument
            self.__dict__['created_at'] = created_at
            self.__dict__['processed_at'] = processed_at
            self.__dict__['processed_quantity'] = processed_quantity
            self.__dict__['avg_price'] = avg_price
            self.__dict__['valid_until'] = valid_until

    def __getattr__(self,
                    name):

        if name not in ['quantity', 'limit_price', 'stop_price', 'type', 'side', 'instrument',
                        'created_at', 'processed_at', 'processed_quantity', 'avg_price', 'valid_until']:

            raise AttributeError(f"'Order' object has no attribute '{name}''")

        orderinfo = _request(method='GET',
                             url=f'https://api.lemon.markets/rest/v1/accounts/{self.account.uuid}/orders/{self.id}/',
                             headers='{"Authorization": "Token %s"}' % self.account.token)
        self.__dict__['quantity'] = orderinfo['quantity']
        self.__dict__['type'] = orderinfo['type']
        self.__dict__['limit_price'] = orderinfo['stop_price'] = None
        if 'limit' in self.__dict__['type']:
            self.__dict__['limit_price'] = orderinfo['limit_price']
        elif 'stop' in self.__dict__['type']:
            self.__dict__['stop_price'] = orderinfo['stop_price']
        self.__dict__['side'] = orderinfo['side']
        self.__dict__['status'] = orderinfo['status']
        self.__dict__['instrument'] = Instrument(orderinfo['instrument']['isin'])
        self.__dict__['created_at'] = orderinfo['created_at']
        self.__dict__['processed_at'] = orderinfo['processed_at']
        self.__dict__['processed_quantity'] = orderinfo['processed_quantity']
        self.__dict__['avg_price'] = orderinfo['average_price']
        self.__dict__['valid_until'] = orderinfo['valid_until']

        return self.__dict__[name]

    def __setattr__(self, key, value):
        if debug:
            print(f"[{ctime()}:DEBUG] The attributes of 'Order' object cannot be set directly. Nothing has been changed")

    def __str__(self):

        return f'Order object, quantity: {self.quantity}, type: {self.type}, limit_price: {self.limit_price}, stop_price: {self.stop_price},'\
            f'side: {self.side}, status: {self.status}, instrument: {self.instrument}, created_at: {self.created_at},'\
            f'processed_at: {self.processed_at}, processed_quantity: {self.processed_quantity}, id: {self.id}, account: {str(self.account)},'\
            f'avg_price: {self.avg_price}, valid_until: {self.valid_until}'

    def __repr__(self):

        return f'Order object, quantity: {self.quantity}, type: {self.type}, limit_price: {self.limit_price}, stop_price: {self.stop_price},'\
            f'side: {self.side}, status: {self.status}, instrument: {self.instrument}, created_at: {self.created_at},'\
            f'processed_at: {self.processed_at}, processed_quantity: {self.processed_quantity}, id: {self.id}, account: {str(self.account)},'\
            f'avg_price: {self.avg_price}, valid_until: {self.valid_until}'


class Portfolio:
    '''An object representing a portfolio

    Args:
        account (Account, required): The Account object representing the account

    Note:
        This class is not intended to be used directly. You can get it by calling :meth:`lemon_markets.Account::get_portfolio`
    '''

    class Position:
        '''A class representing a position in your portfolio

        Args:
            quantity (int, required): The quantity of the instrument in the position
            avg_price (float, required): The average price of one instrument in the position
            instrument (Instrument, required): The instrument in the position
            id (str, required): The id of the position

        Note:
            This class is not intended to be called directly. It is the return of :meth:`lemon_markets.Portfolio.get_aggregated`,
            :meth:`lemon_markets.Portfolio.get_seperated` and :meth:`lemon_markets.Portfolio.get_instrument`
        '''

        def __init__(self, quantity=None, avg_price=None, instrument=None, id=None):

            assert None not in [quantity, avg_price, instrument, id], 'quantity, avg_price, instrument and id must be specified'

            self.quantity = quantity
            self.avg_price = avg_price
            self.instrument = instrument
            self.id = id

        def __str__(self):
            return f'Position object:'\
                f'quantity: {self.quantity},'\
                f'avg_price: {self.avg_price},'\
                f'instrument: {str(self.instrument)},'\
                f'id: {self.id}'

        def __repr__(self):
            return f'Position object:'\
                f'quantity: {self.quantity},'\
                f'avg_price: {self.avg_price},'\
                f'instrument: {str(self.instrument)},'\
                f'id: {self.id}'

    def __init__(self, account=None):

        assert account is not None, 'account must be specified'

        self.account = account

    def get_aggregated(self):
        '''Get all positions in the account aggregated on instruments

        Returns:
            list (Position): A list of all positions
        '''
        r_positions = _request(method='GET',
                               url=f'https://api.lemon.markets/rest/v1/accounts/{self.account.uuid}/portfolio/aggregated',
                               headers=self.account._auth_header)
        returnpositions = [] * len(r_positions)
        for i, result in enumerate(r_positions):
            returnpositions[i] = self.Position(result['quantity'],
                                               result['average_price'],
                                               Instrument(result['instrument']['isin']),
                                               result['uuid'])
        return returnpositions

    def get_seperated(self, limit=200, offset=0):
        '''Get all positions in the Portfolio based on orders

        Args:
            limit (int, optional): The maximum of results to return. Default is 200
            offset (int, optional): How many of the first results to skip. Default is 0

        Returns:
            list (Position): A list of positions
        '''

        pages_list = []
        while limit > 0:
            if limit >= 200:
                pages_list.append(200)
                limit -= 200
            else:
                pages_list.append(limit)
                limit = 0

        portfolio_list = []
        for i, item in enumerate(pages_list):
            page_offset = i * 1000 + offset
            r_aggregated = _request(method='GET',
                                    url=f'https://api.lemon.markets/rest/v1/accounts/{self.account.uuid}/portfolio/',
                                    headers=self._auth_header,
                                    fields={
                                        'limit': item,
                                        'offset': page_offset
                                    })
            portfolio_list += r_aggregated['results']
            if r_aggregated['next'] == 'null':
                break
        returnpositions = [] * len(portfolio_list)
        for i, result in enumerate(portfolio_list):
            returnpositions[i] = self.Position(result['quantity'],
                                               result['average_price'],
                                               Instrument(result['instrument']['isin']),
                                               result['uuid'])
        return returnpositions

    def get_instrument(self, instrument=None):
        '''Get the aggregated position for one instrument in your account

        Args:
            instrument (Instrument, required): The Instrument for which to return it's position

        Returns:
            Position: A Position object representing the aggregated position for the instrument
        '''

        assert instrument is not None, 'instrument must be specified'

        r_instrumentpos = _request(method='GET',
                                   url=f'https://api.lemon.markets/rest/v1/accounts/{self.account.uuid}/portfolio/{instrument.isin}/aggregated/',
                                   headers=self.account._auth_header)
        return self.Position(r_instrumentpos['quantity'],
                             r_instrumentpos['average_price'],
                             Instrument(r_instrumentpos['instrument']['isin']),
                             r_instrumentpos['uuid'])


def get_accounts(token):
    '''Get accounts associated with the given token

    Args:
        token (str, required): The token to search for connected accounts

    Returns:
        list (Account): Accounts associated with the token
    '''

    r_accountlist = _request(method='GET',
                             url='https://api.lemon.markets/rest/v1/accounts/',
                             headers={'Authorization': f'Token {token}'})
    accountlist = []
    for i in r_accountlist['results']:
        accountlist.append(Account(i['uuid'], token))
    if debug:
        print(f'[{ctime()}:DEBUG] Returned {len(accountlist)} accounts')
    return accountlist


def _request(method, url, fields=None, headers=None):

    response = PoolManager(timeout=request_timeout).request(method, url, fields, headers, retries=request_retries)

    if (response.status > 199 and response.status < 300):
        return loads(response.data.decode('utf-8'))
    status_msg = ''
    if (response.status > 299):
        status_msg = 'redirect'
    if (response.status > 399):
        status_msg = 'bad client'
    if (response.status > 499):
        status_msg = 'server error'
    if debug:
        print(response.data.decode('utf-8'))
    raise AssertionError(f'Request failed with status {response.status} ({status_msg})')


if __name__ == '__main__':

    freeze_support()
    time.sleep(0.5)
    if debug:
        print(f'[{ctime()}:DEBUG] Executed freeze_support()')
