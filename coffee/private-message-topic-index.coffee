$ ->
  class Topic
    constructor: (pk) ->
      @pk = pk
      topic = @
      @page = window._initial_page
      @max_pages = 1
      @pagination = window._pagination
      @postHTML = Handlebars.compile(@postHTMLTemplate())
      @paginationHTML = Handlebars.compile(@paginationHTMLTeplate())
      @is_mod = window._is_topic_mod
      @is_logged_in = window._is_logged_in
      
      socket = io.connect('http://' + document.domain + ':3000' + '');
      
      socket.on "connect", () =>
        socket.emit 'join', "pm--#{topic.pk}"
      
      socket.on "console", (data) ->
        console.log data
        
      socket.on "event", (data) ->
        if data.post?
          if topic.page == topic.max_pages
            $("#post-container").append topic.postHTML data.post
          else
            topic.max_pages = Math.ceil data.count/topic.pagination
            topic.page = topic.max_pages
      
      window.socket = socket
      
      do @refreshPosts

      if window._can_edit?
        @inline_editor = new InlineEditor "#new-post-box", "", false
      
        @inline_editor.onSave (html, text) ->
          $.post "/messages/#{topic.pk}/new-post", JSON.stringify({post: html, text: text}), (data) =>
            if data.error?
              topic.inline_editor.flashError data.error
              
            if data.success?
              socket.emit "event", 
                room: "pm--#{topic.pk}"
                post: data.newest_post
                count: data.count
                
              if topic.page == topic.max_pages
                $("#post-container").append topic.postHTML data.newest_post
              else
                topic.max_pages = Math.ceil data.count/topic.pagination
                topic.page = topic.max_pages
                do topic.refreshPosts
      
      $("#post-container").delegate ".post-edit", "click", (e) ->
        e.preventDefault()
        element = $(this)
        post_content = $("#post-"+element.data("pk"))
        post_buttons = $("#post-buttons-"+element.data("pk"))
        post_buttons.hide()
        
        inline_editor = new InlineEditor "#post-"+element.data("pk"), "", true
        
        inline_editor.onSave (html, text, edit_reason) ->
          console.log edit_reason
          $.post "/messages/#{topic.pk}/edit-post", JSON.stringify({pk: element.data("pk"), post: html, text: text}), (data) =>
            if data.error?
              topic.inline_editor.flashError data.error
            
            if data.success?
              inline_editor.destroyEditor()
              post_content.html data.html
              post_buttons.show()
        
        inline_editor.onCancel (html, text) ->
          inline_editor.destroyEditor()
          inline_editor.resetElementHtml()
          post_buttons.show()
                   
      $("nav.pagination-listing").delegate "#previous-page", "click", (e) ->
        e.preventDefault()
        element = $(this)
        if topic.page != 1
          $(".change-page").parent().removeClass("active")
          topic.page--
          do topic.refreshPosts
        
      $("nav.pagination-listing").delegate "#next-page", "click", (e) ->
        e.preventDefault()
        element = $(this)
        if topic.page != topic.max_pages
          $(".change-page").parent().removeClass("active")
          topic.page++
          do topic.refreshPosts
      
      $("nav.pagination-listing").delegate ".change-page", "click", (e) ->
        e.preventDefault()
        element = $(this)
        topic.page = parseInt(element.text())
        do topic.refreshPosts
        
      $("nav.pagination-listing").delegate "#go-to-end", "click", (e) ->
        e.preventDefault()
        element = $(this)
        topic.page = parseInt(topic.max_pages)
        do topic.refreshPosts
        
      $("nav.pagination-listing").delegate "#go-to-start", "click", (e) ->
        e.preventDefault()
        element = $(this)
        topic.page = 1
        do topic.refreshPosts
              
    paginationHTMLTeplate: () ->
      return """
          <ul class="pagination">
            <li>
              <a href="#" aria-label="Start" id="go-to-start">
                <span aria-hidden="true">Go to Start</span>
              </a>
            </li>
            <li>
              <a href="#" aria-label="Previous" id="previous-page">
                <span aria-hidden="true">&laquo;</span>
              </a>
            </li>
            {{#each pages}}
            <li><a href="#" class="change-page page-link-{{this}}">{{this}}</a></li>
            {{/each}}
            <li>
              <a href="#" aria-label="Next" id="next-page">
                <span aria-hidden="true">&raquo;</span>
              </a>
            </li>
            <li>
              <a href="#" aria-label="End" id="go-to-end">
                <span aria-hidden="true">Go to End</span>
              </a>
            </li>
          </ul>
      """
    
    postHTMLTemplate: () ->
      return """
            <li class="list-group-item post-listing-info">
              <div class="row">
                <div class="col-xs-4 hidden-md hidden-lg">
                  <img src="{{user_avatar_60}}" width="{{user_avatar_x_60}}" height="{{user_avatar_y_60}}" class="avatar-mini">
                </div>
                <div class="col-md-3 col-xs-8">
                  {{#if author_online}}
                  <b><span class="glyphicon glyphicon-ok-sign" aria-hidden="true"></span> <a href="/member/{{author_login_name}}">{{author_name}}</a></b>
                  {{else}}
                  <b><span class="glyphicon glyphicon-minus-sign" aria-hidden="true"></span> <a href="/member/{{author_login_name}}" class="inherit_colors">{{author_name}}</a></b>
                  {{/if}}
                  {{#unless author_group_name}}
                  <span style="color:#F88379;"><strong>Members</strong></span><br>
                  {{else}}
                  {{group_pre_html}}{{author_group_name}}{{group_post_html}}
                  {{/unless}}
                  <span class="hidden-md hidden-lg">Posted {{created}}</span>
                </div>
                <div class="col-md-9 hidden-xs hidden-sm">
                  <span id="post-number-1" class="post-number" style="vertical-align: top;"><a href="{{direct_url}}">\#{{count}}</a></span>
                  Posted {{created}}
                </div>
              </div>
            </li>
            <li class="list-group-item post-listing-post">
              <div class="row">
                <div class="col-lg-3 col-md-4" style="text-align: center;">
                  <img src="{{user_avatar}}" width="{{user_avatar_x}}" height="{{user_avatar_y}}" class="post-member-avatar hidden-xs hidden-sm">
                  <span class="hidden-xs hidden-sm"><br><br>
                  <div class="post-member-self-title">{{user_title}}</div>
                    <hr></span>
                  <div class="post-meta">
                  </div>
                </div>
                <div class="col-lg-9 col-md-8 post-right">
                  <div class=".post-content" id="post-{{_id}}">
                    {{{html}}}
                  </div>
                  <br>
                  <div class="row post-edit-likes-info" id="post-buttons-{{_id}}">
                      <div class="col-md-8">
                        {{#if _is_logged_in}}
                        <div class="btn-group" role="group" aria-label="...">
                          <button type="button" class="btn btn-default">Report</button>
                          <div class="btn-group">
                            <button type="button" class="btn btn-default">Reply</button>
                            <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                              <span class="caret"></span>
                              <span class="sr-only">Toggle Dropdown</span>
                            </button>
                            <ul class="dropdown-menu" role="menu">
                              <li><a href="#">Quote</a></li>
                            </ul>
                          </div>
                        {{/if}}
                          <div class="btn-group" style="">
                            {{#if _is_topic_mod}}
                            <button type="button" class="btn btn-default">Options</button>
                            <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                              <span class="caret"></span>
                              <span class="sr-only">Toggle Dropdown</span>
                            </button>
                            <ul class="dropdown-menu" role="menu">
                                  <li><a href="#" class="post-edit" data-pk="{{_id}}">Edit</a></li>
                            </ul>
                            {{else}}
                              {{#if is_author}}
                                <button type="button" class="btn btn-default">Options</button>
                                <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                                  <span class="caret"></span>
                                  <span class="sr-only">Toggle Dropdown</span>
                                </button>
                                <ul class="dropdown-menu" role="menu">
                                  <li><a href="#" class="post-edit" data-pk="{{_id}}">Edit</a></li>
                                </ul>
                              {{/if}}
                            {{/if}}
                          </div>
                        </div>
                    </div>
                    <div class="col-md-4 post-likes">
                    </div>
                  </div>
                  <hr>
                  <div class="post-signature">
                  </div>
                </div>
      """
      
    refreshPosts: () ->
      new_post_html = ""
      $.post "/messages/#{@pk}/posts", JSON.stringify({page: @page, pagination: @pagination}), (data) =>
        history.pushState({id: "pm-#{@pk}-page-#{@page}"}, '', "/messages/#{@pk}/page/#{@page}");
        first_post = ((@page-1)*@pagination)+1
        for post, i in data.posts
          post.count = first_post+i
          post._is_topic_mod = @is_mod
          post._is_logged_in = @is_logged_in
          post.direct_url = "/messages/#{@pk}/"
          new_post_html = new_post_html + @postHTML post
        
        pages = []
        @max_pages = Math.ceil data.count/@pagination
        if @max_pages > 5
          if @page > 3 and @page < @max_pages-5
            pages = [@page-2..@page+5]
          else if @page > 3
            pages = [@page-2..@max_pages]
          else if @page <= 3
            pages = [1..@page+5]
        else
          pages = [1..Math.ceil data.count/@pagination]
        pagination_html = @paginationHTML {pages: pages}
        
        $("#topic-breadcrumb")[0].scrollIntoView()
        $(".pagination-listing").html pagination_html
        $("#post-container").html new_post_html
        $(".page-link-#{@page}").parent().addClass("active")
                
  window.topic = new Topic($("#post-container").data("pk"))