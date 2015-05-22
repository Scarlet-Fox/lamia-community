$ ->
  class Topic
    constructor: (slug) ->
      @slug = slug
      topic = @
      @page = 1
      @max_pages = 1
      @pagination = window._pagination
      @postHTML = Handlebars.compile(@postHTMLTemplate())
      @paginationHTML = Handlebars.compile(@paginationHTMLTeplate())
      @is_mod = window._is_topic_mod
      @is_logged_in = window._is_logged_in
      
      do @refreshPosts
      
    paginationHTMLTeplate: () ->
      return """
          <ul class="pagination">
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
                <div class="col-md-3" style="text-align: center;">
                  <img src="{{user_avatar}}" width="{{user_avatar_x}}" height="{{user_avatar_y}}" class="post-member-avatar hidden-xs hidden-sm">
                  <span class="hidden-xs hidden-sm"><br><br>
                  <div class="post-member-self-title">{{user_title}}</div>
                    <hr></span>
                  <div class="post-meta">
                  </div>
                </div>
                <div class="col-md-9 post-right">
                  <div class=".post-content" id="post-{{_id}}">
                    {{{html}}}
                  </div>
                  <br>
                  <div class="row post-edit-likes-info">
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
                              <li><a href="#">Multiquote</a></li>
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
                              <li><a href="#">Edit</a></li>
                              <li><a href="#">Hide</a></li>
                            </ul>
                            {{else}}
                              {{#if is_author}}
                                <button type="button" class="btn btn-default">Options</button>
                                <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                                  <span class="caret"></span>
                                  <span class="sr-only">Toggle Dropdown</span>
                                </button>
                                <ul class="dropdown-menu" role="menu">
                                  <li><a href="#">Edit</a></li>
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
      $.post "/topic/#{@slug}/posts", JSON.stringify({page: @page, pagination: @pagination}), (data) =>
        first_post = ((@page-1)*@pagination)+1
        for post, i in data.posts
          post.count = first_post+i
          console.log post.count
          post._is_topic_mod = @is_mod
          post._is_logged_in = @is_logged_in
          post.direct_url = "/topic/#{@slug}/page/#{@page}/post/#{post._id}"
          new_post_html = new_post_html + @postHTML post
        
        $("#post-container").html new_post_html
        
  window.topic = new Topic($("#post-container").data("slug"))
