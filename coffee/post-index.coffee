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
                  <img src="{{user_avatar_60}}" width="{{user_avatar_x_60}}" height="{{user_avatar_y_60}}" class="">
                </div>
                <div class="col-md-3 col-xs-8">
                  {{#if author_online}}
                  <b><span class="glyphicon glyphicon-ok-sign" aria-hidden="true"></span> {{author_name}}</b>
                  {{else}}
                  <b><span class="glyphicon glyphicon-minus-sign" aria-hidden="true"></span> {{author_name}}</b>
                  {{/if}}
                  <span style="color:#F88379;"><strong>Members</strong></span><br>
                  <span class="hidden-md hidden-lg">Posted {{created}}</span>
                </div>
                <div class="col-md-9 hidden-xs hidden-sm">
                  <span id="post-number-1" class="post-number" style="vertical-align: top;"><a href="#">#1</a></span>
                  Posted {{created}}
                </div>
              </div>
            </li>
      """
      
    refreshPosts: () ->
      new_post_html = ""
      $.post "/topic/#{@slug}/posts", JSON.stringify({page: @page, pagination: @pagination}), (data) =>
        for post in data.posts
          new_post_html = new_post_html + @postHTML post
        
        $("#post-container").html new_post_html
        
  window.topic = new Topic($("#post-container").data("slug"))