mysql = require('mysql')
fs = require('fs')
moment = require('moment')
{ Pool, Client } = require('pg')

config = JSON.parse(fs.readFileSync('config.json', 'utf8'))


pg_client = new Client
  user: config.pg_user
  host: config.pg_host
  database: config.pg_database
  password: config.pg_password
  port: 5432

do pg_client.connect

mysql_connection = mysql.createConnection
  host     : 'localhost'
  user     : config.import_db_user
  password : config.import_db_password
  database : config.import_db_name
  
do mysql_connection.connect

_get_guest_query = """
  SELECT id FROM public."user"
  WHERE login_name = '_Guest Account_'
  """

_get_posts_query = """
  SELECT * FROM wbb1_post
  ORDER BY time ASC
"""

pg_client.query _get_guest_query, (err, res) =>
  _guest_user_account_id = res.rows[0].id
  
  _t_query = mysql_connection.query _get_posts_query 
  _t_query 
    .on 'error', (err) ->
      console.log err
    .on 'fields', (fields) ->
      console.log
    .on 'result', (row) ->
      do mysql_connection.pause
      
      pg_client.query "SELECT id FROM public.user WHERE legacy_id=#{row.userID}", (err, res) =>
        if res.rows[0]?
          _author_id = res.rows[0].id
        else
          _author_id = _guest_user_account_id
                  
        pg_client.query "SELECT id FROM public.user WHERE legacy_id=#{row.editorID}", (err, res) =>
          if res.rows[0]?
            _editor_id = res.rows[0].id
            modified = moment.utc(row.lastEditTime).format()
          else
            _editor_id = null
            modified = null
            
          html = row.message
          created = row.time
          hidden = row.isDeleted or row.isDisabled or row.isClosed
          topic = row.threadID
          
          _insert_into_db = 'INSERT INTO post(html, created, hidden, topic_id, author_id, editor_id, modified) VALUES($1, to_timestamp($2), $3, $4, $5, $6, $7) RETURNING *'
          _values_into_db = [html, created, hidden, topic, _author_id, _editor_id, modified]
          
          pg_client.query _insert_into_db, _values_into_db, (err, res) =>
            if err
              console.log err.stack
          
            do mysql_connection.resume
    .on 'end', () ->
      do mysql_connection.end
      do pg_client.end
      do process.exit
  


# 

# _query = """
#   SELECT * FROM zuforum.wbb1_post
#   ORDER BY time ASC
#   """



# _query = """
#   SELECT * FROM zuforum.wbb1_post
#   ORDER BY time ASC
#   """
#
# query = connection.query _query
#
# query
#   .on 'error', (err) ->
#     console.log "#{err}\n\n"
#   .on 'fields', (fields) ->
#     console.log "#{fields}\n\n"
#   .on 'result', (row) ->
#     do connection.pause
#     do connection.resume
#   .on 'end', () ->
#     console.log "END"