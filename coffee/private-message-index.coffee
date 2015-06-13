$ ->
  class Messages
    constructor: () ->
      category = @
      @page = 1
      @max_pages = 1
      @pagination = $(".topic-listing").data("pagination")
      @topicHTML = Handlebars.compile(@topicHTMLTemplate())
      @paginationHTML = Handlebars.compile(@paginationHTMLTemplate())
      
      do @refreshTopics
        
      $("nav.pagination-listing").delegate ".change-page", "click", (e) ->
        e.preventDefault()
        element = $(this)
        $(".page-link-#{category.page}").parent().removeClass("active")
        category.page = parseInt(element.text())
        do category.refreshTopics
        
      $("nav.pagination-listing").delegate "#previous-page", "click", (e) ->
        e.preventDefault()
        element = $(this)
        if category.page != 1
          $(".change-page").parent().removeClass("active")
          category.page--
          do category.refreshTopics
        
      $("nav.pagination-listing").delegate "#next-page", "click", (e) ->
        e.preventDefault()
        element = $(this)
        if category.page != category.max_pages
          console.log $(".page-link-#{category.page}").parent().next().children("a").text()
          $(".change-page").parent().removeClass("active")
          category.page++
          do category.refreshTopics
          
    paginationHTMLTemplate: () ->
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
    
    topicHTMLTemplate: () ->
      return """
        <div class="row">
          <div class="col-xs-12 col-sm-6">
            <span class="topic-listing-name">
            <a href="/messages/{{_id}}">{{title}}</a><br>
            <span class="topic-author">
              Started by {{creator}}, {{created}}
            </span>
            <span class="topic-listing-jumps">
              <span class="badge" style=""><a class="inherit_colors" href="#">1</a></span>
              {{#if last_pages}}
              <span class="badge" style="">...</span>
              <span class="badge" style=""><a class="inherit_colors" href="#">{{last_page}}</a></span>
              {{/if}}
            </span>
          </div>
          <div class="col-xs-3 hidden-xs hidden-sm">
            <span class="topic-listing-recent">
              <a href="#" class="topic-listing-text">{{message_count}} replies</a>
            </span>
          </div>
          <div class="col-xs-6 col-sm-3 hidden-xs">
            <span class="topic-listing-recent-image">
              <img src="{{last_post_author_avatar}}" width="{{last_post_x}}px" height="{{last_post_y}}px" class="avatar-mini">
            </span>
            <span class="topic-listing-recent">
              <a href="/member/{{last_post_by_login_name}}" class="topic-listing-username">{{last_post_by}}</a>
              <br>
              <a href="#" class="topic-listing-time">{{last_post_date}}</a>
            </span>
          </div>
        </div>
      </div>
      {{#unless last}}
      <hr>
      {{/unless}}
      """  
      
    refreshTopics: () ->
      new_topic_html = ""
      $.post "/message-topics", JSON.stringify({page: @page, pagination: @pagination}), (data) =>
        for topic, i in data.topics
          if i == data.topics.length-1
            topic.last = true
          topic.last_page = Math.ceil topic.last_page
          new_topic_html = new_topic_html + @topicHTML topic
        pages = [1..Math.ceil data.count/@pagination]
        @max_pages = pages[pages.length-1]
        pagination_html = @paginationHTML {pages: pages}
        
        $(".topic-listing").html(new_topic_html)
        $(".pagination-listing").html(pagination_html)
        $(".page-link-#{@page}").parent().addClass("active")
          
  window.messages = new Messages()
  