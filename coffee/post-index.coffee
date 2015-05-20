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
      
      """
      
    refreshPosts: () ->
      new_post_html = ""
      $.post "/topic/#{@slug}/posts", JSON.stringify({page: @page, pagination: @pagination}), (data) =>
        console.log data
        
  window.topic = new Topic($("#post-container").data("slug"))