express = require 'express'
app = express()
server = require('http').createServer(app)
io = require('socket.io')(server)
bodyParser = require('body-parser')
app.use(bodyParser.json())

key = "32932mklfdsy972@212278"
socketList = new Array()

app.get "/", (req, res) ->
  res.send ''

app.post "/notify", (req, res) ->
  for client in socketList
    try
      if client.user in req.body.users
        client.emit "notify", req.body
    catch
      continue
  res.send 'ok'

io.on 'connection', (client) ->
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

server.listen 3000, () ->
  host = server.address().address
  port = server.address().port

  console.log('Listener at http://%s:%s', host, port)

# var clients_in_the_room = io.sockets.adapter.rooms[roomId];
# for (var clientId in clients_in_the_room ) {
#   console.log('client: %s', clientId); //Seeing is believing
#   var client_socket = io.sockets.connected[clientId];//Do whatever you want with this
# }
