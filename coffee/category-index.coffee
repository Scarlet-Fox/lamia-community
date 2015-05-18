$ ->
  class Category
    constructor: (slug) ->
      @slug = slug
      category = @
      @page = 1
      @pagination = $(".topic-listing").data("pagination")
      @topicHTML = Handlebars.compile(@topicHTMLTemplate())
      
      do @getPreferences
      do @refreshTopics
      
      $("#prefix-filter-show-all").click (e) =>
        e.preventDefault()
        do @disablePrefixFiltering
        
      $(".prefix-filter-action").click (e) ->
        e.preventDefault()
        element = $(this)
        if element.children("span").hasClass "glyphicon-ok"
          element.children("span").removeClass "glyphicon-ok"
          element.children("span").addClass "glyphicon-remove"
        else
          element.children("span").removeClass "glyphicon-remove"
          element.children("span").addClass "glyphicon-ok"
        do category.setPreferences
        
    topicHTMLTemplate: () ->
      return """
        <div class="row">
          <div class="col-xs-12 col-sm-6">
            <span class="topic-listing-name">
            {{#if prefix}}
            {{{pre_html}}}{{{prefix}}}{{{post_html}}}
            {{/if}}
            <a href="#">{{title}}</a><br>
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
              <a href="#" class="topic-listing-text">{{post_count}} replies</a>
              <br>
              <a href="#" class="topic-listing-text">{{view_count}} views</a>
            </span>
          </div>
          <div class="col-xs-6 col-sm-3 hidden-xs">
            <span class="topic-listing-recent-image">
              <img src="{{last_post_author_avatar}}" width="{{last_post_x}}px" height="{{last_post_y}}px">
            </span>
            <span class="topic-listing-recent">
              <a href="/profile/{{last_post_by_login_name}}" class="topic-listing-username">{{last_post_by}}</a>
              <br>
              <a href="#" class="topic-listing-time">{{last_post_date}}</a>
            </span>
          </div>
        </div>
      </div>
      <hr>
      """  
      
    refreshTopics: () ->
      new_topic_html = ""
      $.post "/category/#{@slug}/topics", JSON.stringify({page: @page, pagination: @pagination}), (data) =>
        for topic in data.topics
          new_topic_html = new_topic_html + @topicHTML topic
        $(".topic-listing").html(new_topic_html)
      
    disablePrefixFiltering: () ->
      @preferences = {}
      $(".prefix-filter-action").children("span").removeClass("glyphicon-remove")
      $(".prefix-filter-action").children("span").addClass("glyphicon-ok")
      do @setPreferences
    
    setPreferences: () ->
      @preferences = {}
      category = @
      
      if $(".prefix-filter-action").children(".glyphicon-remove").length > 0
        $(".prefix-filter-action").children(".glyphicon-ok").parent().each () ->
          element = $(this)
          category.preferences[element.data("prefix")] = 1

      $.post "/category/#{@slug}/filter-preferences", JSON.stringify({preferences: @preferences}), (data) =>
        do @refreshTopics
    
    getPreferences: () ->
      $.get "/category/#{@slug}/filter-preferences", (data) =>
        @preferences = data.preferences
        
        if $.isEmptyObject(@preferences)
          do @disablePrefixFiltering
        else
          $(".prefix-filter-action").children("span").removeClass("glyphicon-ok")
          $(".prefix-filter-action").children("span").addClass("glyphicon-remove")
          for prefix of @preferences
            $("[data-prefix='#{prefix}']").children("span").removeClass("glyphicon-remove")
            $("[data-prefix='#{prefix}']").children("span").addClass("glyphicon-ok")
  
  window.category = new Category($(".topic-listing").data("slug"))