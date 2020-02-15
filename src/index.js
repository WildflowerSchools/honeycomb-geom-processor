require("dotenv").config()

const express = require("express")

const auth = require("./auth")
const geoms = require("./geoms")
const errors = require("./errors")
const applyAuth = auth.apply
const applyErrors = errors.apply
const applyGeoms = geoms.apply

const port = process.env.SERVICE_PORT ? process.env.SERVICE_PORT : 8010

let app, server
;(async () => {

  if (process.env.ENVIRONMENT === "production") {
    const http = require("http")
    app = express()
    server = http.createServer(app)
  } else {
    const https = require("https")
    app = require("https-localhost")()
    server = https.createServer(await app.getCerts(), app)
  }

  console.log("setting up")

  applyAuth(app)
  applyErrors(app)
  applyGeoms(server)

  server.listen(port, function() {
    console.log(`Listening on port ${port}!`)
  })
})()
