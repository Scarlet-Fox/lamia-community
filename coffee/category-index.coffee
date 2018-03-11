$ ->
  class Category
    constructor: (slug) ->
      @slug = slug
      category = @
      @page = 1
      @max_pages = 1
      @pagination = $(".topic-listing").data("pagination")
      @topicHTML = Handlebars.compile(@topicHTMLTemplate())
      @paginationHTML = Handlebars.compile(@paginationHTMLTemplate())

      do @getPreferences

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
              <a href="" aria-label="Previous" id="previous-page">
                <span aria-hidden="true">&laquo;</span>
              </a>
            </li>
            {{#each pages}}
            <li><a href="" class="change-page page-link-{{this}}">{{this}}</a></li>
            {{/each}}
            <li>
              <a href="" aria-label="Next" id="next-page">
                <span aria-hidden="true">&raquo;</span>
              </a>
            </li>
          </ul>
      """

    topicHTMLTemplate: () ->
      return """
        <div class="row">
          <div class="col-xs-12 col-sm-5">
            <span class="topic-listing-name">
            {{#if prefix}}
            {{{pre_html}}}
              {{#if sticky}}<span class="glyphicon glyphicon-pushpin" aria-hidden="true"></span>&nbsp;{{/if}}
              {{#if closed}}<span class="glyphicon glyphicon-lock" aria-hidden="true"></span>&nbsp;{{/if}}
              {{{prefix}}}
            {{{post_html}}}
            {{else}}
            {{#if sticky}}<span class="glyphicon glyphicon-pushpin" aria-hidden="true"></span>&nbsp;{{/if}}
            {{#if closed}}<span class="glyphicon glyphicon-lock" aria-hidden="true"></span>&nbsp;{{/if}}
            {{/if}}
            <a href="/t/{{slug}}/page/1/post/last_seen">{{#if updated}}<strong>{{/if}}{{title}}{{#if updated}}</strong>{{/if}}</a><br>
            <span class="topic-author hidden-xs">
              Started by {{creator}}, {{created}}
            </span>
            <span class="topic-author hidden-sm hidden-md hidden-lg">
              <a href="/t/{{slug}}/page/1/post/last_seen">Last Post by {{last_post_by}}&nbsp;&nbsp;|&nbsp;&nbsp;{{last_post_date}}</a>
            </span>
            <span class="topic-listing-jumps hidden-xs hidden-sm">
              <span class="badge" style=""><a class="inherit_colors" href="/t/{{slug}}/page/1">1</a></span>
              {{#if last_pages}}
              <span class="badge" style="">...</span>
              <span class="badge" style=""><a class="inherit_colors" href="/t/{{slug}}/page/1/post/last_seen">{{last_page}}</a></span>
              {{/if}}
            </span>
            <div class="topic-author hidden-xs">
            {{preview}}
            </div>
          </div>
          <div class="col-xs-3 hidden-xs hidden-sm">
            <span class="topic-listing-recent">
              <a href="" class="topic-listing-text">{{post_count}} replies</a>
              <br>
              {{view_count}} views
            </span>
          </div>
          <div class="col-xs-6 col-sm-4 hidden-xs">
            <span class="topic-listing-recent-image subcategory-listing-recent-image">
              <a href="/member/{{last_post_by_login_name}}"><img src="{{last_post_author_avatar}}" width="{{last_post_x}}px" height="{{last_post_y}}px" class="avatar-mini"></a>
            </span>
            <span class="topic-listing-recent">
              <a href="/member/{{last_post_by_login_name}}" class="topic-listing-username hover_user">{{last_post_by}}</a>
              <br>
              <a href="/t/{{slug}}/page/1/post/last_seen" class="topic-listing-time">{{last_post_date}}</a>
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
      $.post "/category/#{@slug}/topics", JSON.stringify({page: @page, pagination: @pagination}), (data) =>
        for topic, i in data.topics
          if i == data.topics.length-1
            topic.last = true
          topic.last_page = Math.ceil topic.last_page
          new_topic_html = new_topic_html + @topicHTML topic
        
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

        $(".topic-listing").html(new_topic_html)
        $(".pagination-listing").html(pagination_html)
        $(".page-link-#{@page}").parent().addClass("active")

    disablePrefixFiltering: () ->
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
        #
        if $.isEmptyObject(@preferences)
          do @disablePrefixFiltering
        else
          $(".prefix-filter-action").children("span").removeClass("glyphicon-ok")
          $(".prefix-filter-action").children("span").addClass("glyphicon-remove")
          for prefix of @preferences
            $("[data-prefix='#{prefix}']").children("span").removeClass("glyphicon-remove")
            $("[data-prefix='#{prefix}']").children("span").addClass("glyphicon-ok")

          do @refreshTopics

  window.category = new Category($(".topic-listing").data("slug"))
