# pylama:ignore=E501

from time import sleep  # some other dependencies

import lemon_markets as lm  # importing lemon_markets as lm


def cb(instrument, trade):  # defining our callback
    print(f'{instrument.name} {trade.time} {trade.price}')


if __name__ == '__main__':  # this is mandatory if you want to use websockets, as it will start multiple threads

    lm.debug = True  # enabling debug messages

    tsla = lm.Instrument('US88160R1014')  # creating an instrument object corresponding to tesla (will be used throughout this tutorial)

    # -------------------------------
    # Printing information about objects
    # -------------------------------

    print('\nInformation about tesla (invoking print on instrument object):')

    print(tsla)  # prints information about the instrument

    # ------------------------
    sleep(10)
    # Demonstrating WebSockets
    # ------------------------

    print('\nStream rt data for tesla using websockets:')

    ws = lm.WebSocket(cb)  # creating a websocket client object with the callback 'cb'

    ws.subscribe(tsla)  # subscribe to rt data from tesla

    sleep(30)  # waiting for 30 sec

    del ws  # deleting the websocket, which in turn disables it

    # ----------
    sleep(10)
    # Using REST
    # ----------

    print('Getting the highest price over the last minute for tesla')

    rst = lm.REST()  # initiating the REST object

    candle = rst.get_m1_candlestick_latest(tsla)  # get the latest ohlc candlestick for tesla

    print(candle.high)  # print the highest price over the last minute
