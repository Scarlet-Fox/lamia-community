express = require 'express'
app = express()
server = require('http').createServer(app)
io = require('socket.io')(server)
bodyParser = require('body-parser')
app.use(bodyParser.json())

key = "32932mklfdsy972@212278"

app.get "/", (req, res) ->
  res.send ''
  
app.post "/notify", (req, res) ->
  console.log req.body
  res.send 'ok'

io.on 'connection', (client) ->
  console.log "We have a live one!"
  
  client.on "join", (data) ->
    client.join data
    client.emit 'console', data
    
  client.on "event", (data) ->
    room = data.room
    console.log data
    client.broadcast.to(room).emit("event", data)
    
server.listen 3000, () ->
  host = server.address().address
  port = server.address().port

  console.log('Example app listening at http://%s:%s', host, port)

# var clients_in_the_room = io.sockets.adapter.rooms[roomId];
# for (var clientId in clients_in_the_room ) {
#   console.log('client: %s', clientId); //Seeing is believing
#   var client_socket = io.sockets.connected[clientId];//Do whatever you want with this
# }
