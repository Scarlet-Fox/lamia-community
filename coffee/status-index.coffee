$ ->
  $grid = $('#status-container');
  window.grid = $grid
  $grid.shuffle
    itemSelector: '.status-index-panel'
    speed: 0

  statusHTMLTemplate = """
  <div class="col-md-4 col-sm-6 status-index-panel">
    <div class="panel panel-default">
      <div class="panel-body">
        <div class="media-left"><a href="{{profile_address}}"><img src="{{user_avatar}}" width="{{user_avatar_x}}px" height="{{user_avatar_y}}px" class="media-object avatar-mini"></a>
        </div>
        <div class="media-body"><a href="{{profile_address}}" class="hover_user">{{user_name}}</a>
        {{#unless attached_to_user}}
        <span>&nbsp;says:</span>
        {{else}}
        <span>&nbsp;says to <a href="{{attached_to_user_url}}" class="hover_user">{{attached_to_user}}</a>:</span>
        {{/unless}}
        <span class="discuss"><a href="/status/{{id}}" class="status-reply-time float-right">Discuss{{#if comment_count}} ({{comment_count}}){{/if}}</a></span><br><span class="status-message">
        {{#if ipb}}
        <p>{{{message}}}</p>
        {{else}}
        <span>{{{message}}}</span>
        {{/if}}  
        </span><span class="status-reply-time"><a href="/status/{{id}}">{{created}}</a></span>
        </div>
      </div>
    </div>
  </div>
  """
  
  statusHTML = Handlebars.compile(statusHTMLTemplate)

  if window.authors.length > 0
    for author in window.authors
      _option = """<option value="#{author.id}" selected="selected">#{author.text}</option>"""
      $(".by-who").append _option 
      $(".by-who-two").append _option  
  
  $(".search-for").val(window.search)
  
  $(".how-many").val(window.count)
  
  select_options = 
    ajax:
      url: "/user-list-api",
      dataType: 'json',
      delay: 250,
      data: (params) ->
        return {
          q: params.term
        }
      processResults: (data, page) ->
        console.log {
          results: data.results
        }
        return {
          results: data.results
        }
      cache: true
    minimumInputLength: 2
  
  $(".by-who").select2 select_options 
  $(".by-who-two").select2 select_options 
    
  $(".how-many").change (e) ->
    console.log $(this).val()
    
  $(".update-statuses").click (e) ->
    e.preventDefault()
    how_many = $(this).parent().parent().find(".how-many").val()
    authors = $(this).parent().parent().find(".author").val()
    search = $(this).parent().parent().find(".search-for").val()
    
    $.post "/status-updates", JSON.stringify({ count: how_many, authors: authors, search: search}), (data) ->
      $('#msg-container').html("")
      $grid.shuffle("remove", $('.status-index-panel'))
      if data.status_updates.length == 0
        $('#msg-container').html("<p>No results...</p>")
      else
        items = []
        for status, i in data.status_updates
          if i == 0
            items = $(statusHTML(status))
          else
            items = items.add(statusHTML(status))
        $('#status-container').append(items)
        setTimeout () ->
          $('#status-container').shuffle('appended', items)
          $('#filtering-header')[0].scrollIntoView()
        , 0
        # $('#status-container').shuffle('update')
        #   $('#status-container').append($(statusHTML(status)))
        # $('#status-container').shuffle("update")
        #
      