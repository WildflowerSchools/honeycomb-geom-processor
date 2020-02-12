require("dotenv").config()

const express = require("express")
const https = require("https")

const auth = require("./auth")
const geoms = require("./geoms")
const errors = require("./errors")
const applyAuth = auth.apply
const applyErrors = errors.apply
const applyGeoms = geoms.apply

const port = process.env.SERVICE_PORT ? process.env.SERVICE_PORT : 8010

let app
;(async () => {
  if (process.env.ENVIRONMENT === "production") {
    app = express()
  } else {
    app = require("https-localhost")()
  }

  console.log("setting up")

  applyAuth(app)
  applyErrors(app)

  const certs = await app.getCerts()
  const server = https.createServer(certs, app)

  applyGeoms(server)

  server.listen(port, function() {
    console.log(`Listening on port ${port}!`)
  })
})()
