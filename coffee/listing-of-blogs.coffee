$ ->
  $grid = $('#blog-container')
  window.grid = $grid
  $grid.shuffle
    itemSelector: '.blog-index-panel'
    speed: 0

  blogHTMLTemplate = """
  <div class="col-xs-6 blog-index-panel">
    <div class="panel panel-default">
      <div class="panel-body">
        <center>
          <div class="media-left"><img src="{{recent_entry_avatar}}" width="{{recent_entry_avatar_x}}" height="{{recent_entry_avatar_y}}" /></div>
          <div class="media-body">
            <a href="/blogs/{{slug}}">{{name}}</a>
            <br>
            <a href="/blogs/{{slug}}/{{recent_entry_slug}}">{{recent_entry_title}}</a>
            <br>
            <span class="text-muted">{{recent_entry_time}}</span>
          </div>
          <br>
          <p class="blog-preview-text">{{{recent_entry_content}}}</p>
        </center>
      </div>
    </div>
  </div>
  """
  
  blogHTML = Handlebars.compile(blogHTMLTemplate)

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
    
  $(".update-blogs").click (e) ->
    e.preventDefault()
    how_many = $(this).parent().parent().find(".how-many").val()
    authors = $(this).parent().parent().find(".author").val()
    search = $(this).parent().parent().find(".search-for").val()
    
    $.post "/blogs", JSON.stringify({ count: how_many, authors: authors, search: search}), (data) ->
      $('#msg-container').html("")
      if $('.blog-index-panel').length > 0
        $grid.shuffle("remove", $('.blog-index-panel'))
      if data.blogs.length == 0
        $('#msg-container').html("<p>No results...</p>")
      else
        items = []
        for blog, i in data.blogs
          if i == 0
            items = $(blogHTML(blog))
          else
            items = items.add(blogHTML(blog))
        $('#blog-container').append(items)
        $('#blog-container').css
          height: count/2*200
        $('.blog-index-panel').dotdotdot({height: 400, after: ".readmore"})
        setTimeout () ->
          $('#blog-container').shuffle('appended', items)
          $('#blog-container').shuffle('update')
          # $('#filtering-header')[0].scrollIntoView()
        , 0
        
  $(".update-blogs-two").click (e) ->
    e.preventDefault()
    how_many = $(this).parent().parent().find(".how-many").val()
    authors = $(this).parent().parent().find(".author").val()
    search = $(this).parent().parent().find(".search-for").val()
    
    $.post "/blogs", JSON.stringify({ count: how_many, authors: authors, search: search}), (data) ->
      $('#msg-container').html("")
      if $('.blog-index-panel').length > 0
        $grid.shuffle("remove", $('.blog-index-panel'))
      if data.blogs.length == 0
        $('#msg-container').html("<p>No results...</p>")
      else
        items = []
        for blog, i in data.blogs
          if i == 0
            items = $(blogHTML(blog))
          else
            items = items.add(blogHTML(blog))
        $('#blog-container').append(items)
        $('#blog-container').css
          height: count/2*200
        $('.blog-index-panel').dotdotdot({height: 200, after: ".readmore"})
        setTimeout () ->
          $('#blog-container').shuffle('appended', items)
          $('#blog-container').shuffle('update')
          # $('#filtering-header')[0].scrollIntoView()
        , 0

  $(".update-blogs").click()