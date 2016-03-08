"use strict"

const autobahn = require('autobahn')
const Events = require('./events')

let events = new Events()

const connection = new autobahn.Connection({
   url: "wss://api.poloniex.com",
   realm: "realm1"
});

connection.onclose = function (reason, details) {
  console.warn("Connection closed: " + reason, details)
  console.warn("Reconnecting...")
  setTimeout(() => connection.open(), 5*1000)
}

connection.onopen = function (session) {

  console.warn("Connected")

   session.subscribe('footer', (e) => {
     events.store('exchange-stats', [e]);
   });

   session.subscribe('ticker', (e) => {
     if (e[0] != 'BTC_ETH') return
     let tickerEvents = [e]
     tickerEvents = tickerEvents.map(e => {
       return {
         last: e[1],
         lowestAsk: e[2],
         highestBid: e[3],
         percentChange: e[4],
         baseVolume: e[5],
         quoteVolume: e[6],
         isFrozen: e[7],
         high24hr: e[8],
         low24hr: e[9]
       }
     })
     events.store('ticker', tickerEvents);
   });

   session.subscribe('BTC_ETH', (e) => {
     events.store('trades', e)
   });
};

connection.open();
