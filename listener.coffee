express = require 'express'
app = express()
fs = require 'fs'
bodyParser = require('body-parser')
app.use(bodyParser.json())

key = "32932mklfdsy972@212278"
socketList = new Array()

config = JSON.parse(fs.readFileSync('config.json', 'utf8'))

server = require('http').createServer(app)
io = require('socket.io')(server, {path: config.listener_path})

app.use (req, res, next) ->
  do next

app.get config.talker_path, (req, res) ->
  res.send ''

app.post config.talker_path+"/notify", (req, res) ->
  res.send 'ok'
  for client in socketList
    try
      if client.user in req.body.users
        req_temp = JSON.parse(JSON.stringify(req.body))
        req_temp.count = req_temp.count[client.user]
        req_temp.dashboard_count = req_temp.dashboard_count[client.user]
        client.emit "notify", req_temp
    catch
      continue

io.on 'connection', (client) ->
  #console.log client
  client.on "user", (data) ->
    socketList.push client
    if socketList.length > 10000
      socketList.shift()
    client.user = data.user

  client.on "join", (data) ->
    client.join data

  client.on "disconnect", () ->
    for socket, i in socketList
      try
        if socket.id == client.id
          socketList.splice(i, 1)
      catch
        continue

  client.on "event", (data) ->
    room = data.room
    client.broadcast.to(room).emit("event", data)

app.listen 3001, () ->
  console.log('Listener at http://%s:%s', server.address().address, 3001)

server.listen 3000, () ->
  host = server.address().address
  port = server.address().port

  console.log('Listener at http://%s:%s', host, 3000)

# var clients_in_the_room = io.sockets.adapter.rooms[roomId];
# for (var clientId in clients_in_the_room ) {
#   console.log('client: %s', clientId); //Seeing is believing
#   var client_socket = io.sockets.connected[clientId];//Do whatever you want with this
# }
