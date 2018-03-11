mysql = require('mysql')
fs = require('fs')
moment = require('moment')
slugify = require('slug')
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


_get_available_topic_slug = (title, f) =>
  _starting_slug = slugify(title, {lower: true})
  if _starting_slug.trim() == ""
    _starting_slug = "_"
  try_slug = (_slug, count=0) =>
    new_slug = _slug
    if count+0 > 0
      new_slug = new_slug+"-"+count
      
    pg_client.query "SELECT COUNT(id) FROM topic WHERE slug='#{new_slug}'", (err, res) =>      
      if res.rows[0].count > 0
        try_slug(_slug, count+1)
      else
        f(new_slug)
        
  try_slug _starting_slug      
  
# _get_available_topic_slug "Introduce Yourself", (available_slug) ->
#   console.log available_slug
#   do process.exit

_get_guest_query = """
  SELECT id FROM public."user"
  WHERE login_name = '_Guest Account_'
"""

_get_topics_query = """
  SELECT t.*,
  board.title AS board_name
  FROM zuforum.wbb1_thread t
  JOIN zuforum.wbb1_board board ON t.boardID = board.boardID
"""

pg_client.query _get_guest_query, (err, res) =>
  _guest_user_account_id = res.rows[0].id

  _t_query = mysql_connection.query _get_topics_query
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
          
        _board_slug = slugify(row.board_name, {lower: true, charmap: {"'": "-"}, multicharmap: {}})
        
        if _board_slug of config.import_db_topic_board_name_mapping
          _board_slug = config.import_db_topic_board_name_mapping[_board_slug ]
        if _board_slug.trim() == ""
          _board_slug = "_"
                  
        pg_client.query "SELECT id FROM category WHERE slug='#{_board_slug}'", (err, res) =>
          if res.rows[0]?
            _category_id = res.rows[0].id
          else
            console.log "Could not find board with slug: "
            console.log _board_slug 
            console.log
            do process.exit
            
          title = row.topic
          
          _get_available_topic_slug title, (slug) =>
            id = row.threadID
            sticky = row.isSticky
            announcement = row.isAnnouncement
            hidden = row.isDeleted or row.isDisabled
            locked = row.isClosed or row.isDisabled
            created = moment.utc(row.time).format()
            
            _insert_into_db = 'INSERT INTO topic(id, sticky, announcement, hidden, locked, created, title, slug, category_id, author_id) VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) RETURNING *'
            _values_into_db = [id, sticky, announcement, hidden, locked, created, title, slug, _category_id, _author_id]
          
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