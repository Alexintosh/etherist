"use strict"

const fs = require('fs')
const dataDir = __dirname + '/../data'

class Events {
  store(type, events, options) {
    events.forEach(e => {
      if (!e._ts) e._ts = Date.now()
    })
    const data = events.map(e => JSON.stringify(e)).join("\n")
    fs.appendFileSync(dataDir + '/' + type + '.jsons', data + "\n");
  }
  get(type, options) {
    let data = fs.readFileSync(dataDir + '/' + type + '.jsons', data + "\n");
    return data.split("\n").map(e => JSON.parse(e))
  }
}

module.exports = Events
