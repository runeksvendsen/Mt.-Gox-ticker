#!/usr/bin/env python
import websocket
import thread
import time
import signal
import sys
import datetime
import ast
import argparse

##TODO: Unsubscribe from not used feeds
##    https://bitcointalk.org/index.php?topic=5855.0;all

volume_avg = 100
prev_trades = {'trades' : [], 'volume' : 0.0}

args = None

URL="ws://websocket.mtgox.com/mtgox"
ws = websocket

message_trade = "dbf1dee9-4f2e-4a08-8cb7-748919a71b21"

FILEPATH = '/home/rune/Programming/scripts/mtgox.log'
STATS = '/home/rune/Desktop/stats.txt'

closing = False

def on_trade(trade):
   global args, prev_trades

   if args.debug == True:
      print "--Trade!"

   if (trade['price_currency'] != "USD"):
      print "trade['price_currency'] != \"USD\""
      return

   price = float(trade['price_int'])/1e5
   amount = float(trade['amount_int'])/1e8
   #average price for the last volume_avg Bitcoins sold
   avg_vol_price = -1.0
   
   #newest trade is first item in list
   prev_trades['trades'].insert(0, [price, amount])
   
   prev_trades['volume'] += amount

   while (prev_trades['volume'] - prev_trades['trades'][-1][1]) >= volume_avg:
      prev_trades['volume'] -= prev_trades['trades'].pop()[1]
      
   if (prev_trades['volume'] >= volume_avg):
      avg_vol_price = 0
      for tmptrade in prev_trades['trades']:
         avg_vol_price += tmptrade[0]*tmptrade[1]

      if args.write_stats == True:
         f = open(STATS, 'a')
         f.seek(0,2)
         print >>f, "%d\t%f\t%f\t%f" % (int(trade['date']), price, (avg_vol_price / prev_trades['volume']), prev_trades['volume'])
         f.close()

      avg_vol_price = "%.2f" % (avg_vol_price / prev_trades['volume'])

      if args.debug == True:
         print "--avg_volumes: " + str(prev_trades['volume'])
   else:
      avg_vol_price = "*%.1f" % prev_trades['volume']

   trade_string = "%s %s %s (%s)" % (datetime.datetime.fromtimestamp(int(trade['date'])).strftime('%H:%M:%S'),
                              str(price),
                              str(amount),
                              avg_vol_price)

   if args.one_line == False:
      print trade_string
   else:
      print >> sys.stdout, "\r" + trade_string,
      sys.stdout.flush()

   if args.write_to_file == True:
      f = open(FILEPATH, 'w')
      print >>f, "<span font=\"Monospace\" color=\"green\">%s</span>" % trade_string
      f.close()


def on_message(ws, message):
   #global args

   #if args.debug == True:
   #   print "Message received!"

   #convert received message string into msg dictionary
   msg = ast.literal_eval(message)
   if msg['channel'] == message_trade and msg['op'] != "subscribe":
      on_trade(msg['trade'])

def on_error(ws, error):
   print "dir(error): " + dir(error)

def on_close(ws):
   global closing
   print "### Connection closed ###"
   if args.write_to_file == True:
      f = open(FILEPATH, 'w')
      print >>f, "### Connection closed ###"
      f.close()
   if closing == True:
      sys.exit(0)
   else:
      print "### Retrying in 5 sec... ###"
      if args.write_to_file == True:
         f = open(FILEPATH, 'w')
         print >>f, "### Retrying in 5 sec... ###"
         f.close()
      time.sleep(5)
      ws = websocket.WebSocketApp(URL,
                                   on_message = on_message,
                                   on_error = on_error,
                                   on_close = on_close)
      ws.on_open = on_open
      ws.run_forever()

def on_open(ws):
   global args
   
   print "### Connection opened ###"
   if args.write_to_file == True:
      f = open(FILEPATH, 'w')
      print >>f, "### Connection opened ###"
      f.close()

def program_exit(signal, frame):
   global closing
   closing = True
   print "Closing connection..."
   ws.close()

def main(): 
   parser = argparse.ArgumentParser(description='Display real-time trade data from Mt. Gox.')
   parser.add_argument('-o', '--one-line', action='store_true', help='keep output on one line')
   parser.add_argument('-d', '--debug', action='store_true', help='show debug messages')
   parser.add_argument('-f', '--write-to-file', action='store_true', help='write output to file')
   parser.add_argument('-s', '--write-stats', action='store_true', help='write statistics to file')
   
   global args
   args = parser.parse_args()

   #handle Ctrl+C:
   signal.signal(signal.SIGINT, program_exit)
   signal.signal(signal.SIGTERM, program_exit)

   ws = websocket.WebSocketApp(URL,
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
   ws.on_open = on_open
   ws.run_forever()

if __name__ == "__main__":
    main()
