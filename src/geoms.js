const WebSocket = require("ws")
const securedSessionOrJWT = require("./auth").securedSessionOrJWT
const validateJWT = require("./auth").validateJWT
const handle = require("./handle")

const wss = new WebSocket.Server({
  clientTracking: false,
  noServer: true,
  path: "/ws"
  // verifyClient: (info, done) => {
  //   securedSessionOrJWT(info.req, done, () => {
  //     done(info.req.session)
  //   })
  // }
})

const heartbeat = ws => {
  ws.isAlive = true
}

const sendMessage = (ws, eventName, data) => {
  const msg = JSON.stringify({
    event: eventName,
    data: data
  })
  ws.send(msg)
  console.log(`Sent message ${msg}`)
}

const handleGetGeoms = async (ws, data) => {
  const sample = await handle.fetchSample(data.environment_id, data.date)
  const geoms = await handle.fetchGeomsForSample(sample.id)
  sendMessage(ws, "geoms", {
    sample: sample,
    geoms: geoms
  })
}

const handleGetCoordinates = async (ws, data) => {
  const coordinates = await handle.fetchCoordinatesForSampleAndDeviceWithTime(
    data.sample_id,
    data.device_id,
    data.from
  )

  const grouped = coordinates.reduce((acc, c) => {
    if (!acc.hasOwnProperty(c.geom_id)) {
      acc[c.geom_id] = {}
    }
    acc[c.geom_id][c.time] = c
    return acc
  }, {})
  sendMessage(ws, "coordinates", grouped)
}

const handleWSConnection = wss => {
  wss.on("connection", function(ws, request) {
    ws.isAlive = true
    ws.isAuthenticated = false

    ws.on("message", async function(message) {
      const parsedMsg = JSON.parse(message)
      console.log(`Received message ${message}`)

      if (parsedMsg.event === "ping") {
        sendMessage(ws, "pong", parsedMsg.data)
        heartbeat(ws)
        return
      }

      if (parsedMsg.event === "auth") {
        await validateJWT(parsedMsg.data.Authorization, (err, decoded) => {
          if (err) {
            console.error(`Authorization attempt failed: ${err}`)
          } else {
            ws.isAuthenticated = true
            sendMessage(ws, "authorized", {})
          }
        })
      }

      if (!ws.isAuthenticated) {
        sendMessage(ws, "error", { message: "Unauthorized", code: 4401 })
        return
      }

      switch (parsedMsg.event) {
        case "getGeoms":
          handleGetGeoms(ws, parsedMsg.data)
          return
        case "getCoordinates":
          handleGetCoordinates(ws, parsedMsg.data)
          return
      }
    })

    ws.on("close", function() {})
  })
}

// Expect client to ping once a minute
setInterval(() => {
  if (!wss.clients) {
    return
  }
  wss.clients.forEach(function each(ws) {
    if (ws.isAlive === false) {
      return ws.terminate()
    }

    ws.isAlive = false
  })
}, 60000)

exports.apply = function(server) {
  server.on("upgrade", function(request, socket, head) {
    console.log("Parsing session from request...")

    // sessionParser(request, {}, () => {
    //   if (!request.session.userId) {
    //     socket.destroy();
    //     return;
    //   }

    wss.handleUpgrade(request, socket, head, ws => {
      wss.emit("connection", ws, request)
    })
  })

  handleWSConnection(wss)
}
