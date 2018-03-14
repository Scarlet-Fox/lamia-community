$ ->
  $(".variable-option").hide()
  $(".posts-option").show()
  page = 1
  max_pages = 1

  $("#start-date").datepicker
    format: "m/d/yy"
    clearBtn: true
  $("#end-date").datepicker
    format: "m/d/yy"
    clearBtn: true

  $("#content-search").change (e) ->
    content_type = $(this).val()
    if content_type == "posts"
      $(".variable-option").hide()
      $(".posts-option").show()
    else if content_type == "topics"
      $(".variable-option").hide()
      $(".topics-option").show()
    else if content_type == "status"
      $(".variable-option").hide()
    else if content_type == "blogs"
      $(".variable-option").hide()
      $(".blogs-option").show()
    else if content_type == "messages"
      $(".variable-option").hide()
      $(".messages-option").show()

  if window.authors.length > 0
    for author in window.authors
      _option = """<option value="#{author.id}" selected="selected">#{author.text}</option>"""
      $("#author-select").append _option

  $("#author-select").select2
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

  if window.categories.length > 0
    for category in window.categories
      _option = """<option value="#{category.id}" selected="selected">#{category.text}</option>"""
      $("#category-select").append _option

  if window.topics.length > 0
    for topic in window.topics
      _option = """<option value="#{topic.id}" selected="selected">#{topic.text}</option>"""
      if window.content_type == "posts"
        $("#topic-select").append _option
      else
        $("#pm-topic-select").append _option

  $("#topic-select").select2
    ajax:
      url: "/topic-list-api",
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

  $("#category-select").select2
    ajax:
      url: "/category-list-api",
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

  $("#blog-select").select2
    ajax:
      url: "/blog-list-api",
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

  $("#pm-topic-select").select2
    ajax:
      url: "/pm-topic-list-api",
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

  $("#search-for").val(window.search_for)
  $("#content-search").val(window.content_type)
  $("#start-date").val(window.start_date)
  $("#end-date").val(window.end_date)

  resultTemplateHTML = () ->
    return """
    <ul class="list-group">
      <li class="list-group-item">
        <p>
          <b>
            <a href="{{url}}" class="search-result-title">{{title}}</a>
          </b>
        </p>
        <div class="search-result-content">
            {{{description}}}
            {{#if readmore}}
            <a href="{{url}}" class="readmore">
              <br><b>Read more »</b><br>
            </a>
            {{/if}}
        </div>
        <p class="text-muted">by <a class="hover_user" href="/member/{{author_profile_link}}">{{author_name}}</a> - <a href="{{url}}">{{time}}</a>
        </p>
      </li>
    </ul>
    """
  resultTemplate = Handlebars.compile(resultTemplateHTML())

  paginationForPostsHTMLTemplate = () ->
    return """
        <ul class="pagination">
          <li>
            <a href="" aria-label="Previous" class="previous-page">
              <span aria-hidden="true">Previous Page</span>
            </a>
          </li>
          <li>
            <a href="" aria-label="Next" class="next-page">
              <span aria-hidden="true">Next Page</span>
            </a>
          </li>
        </ul>
    """
  paginationForPostsTemplate = Handlebars.compile(paginationForPostsHTMLTemplate())

  paginationHTMLTemplate = () ->
    return """
        <ul class="pagination">
          <li>
            <a href="" aria-label="Start" class="go-to-start">
              <span aria-hidden="true">Go to Start</span>
            </a>
          </li>
          <li>
            <a href="" aria-label="Previous" class="previous-page">
              <span aria-hidden="true">&laquo;</span>
            </a>
          </li>
          {{#each pages}}
          <li><a href="" class="change-page page-link-{{this}}">{{this}}</a></li>
          {{/each}}
          <li>
            <a href="" aria-label="Next" class="next-page">
              <span aria-hidden="true">&raquo;</span>
            </a>
          </li>
          <li>
            <a href="" aria-label="End" class="go-to-end">
              <span aria-hidden="true">Go to End</span>
            </a>
          </li>
        </ul>
    """
  paginationTemplate = Handlebars.compile(paginationHTMLTemplate())

  updateSearch = () ->
    content_type = $("#content-search").val()

    data =
      q: $("#search-for").val()
      content_type: content_type
      page: page
      authors: $("#author-select").val()

    if $("#start-date").val() != ""
      data["start_date"] = $("#start-date").val()

    if $("#end-date").val() != ""
      data["end_date"] = $("#end-date").val()

    if content_type == "messages"
      data["topics"] = $("#pm-topic-select").val()

    if content_type == "posts"
      data["topics"] = $("#topic-select").val()
      # data["categories"] = $("#category-select").val()

    if content_type == "topics"
      data["categories"] = $("#category-select").val()

    if content_type == "blogs"
      data["blogs"] = $("#blog-select").val()
      
    $("#search-results").hide()
    $("#search-spinner").show()
    $("#results-header").text("Searching...")

    $.post "/search", JSON.stringify(data), (data) ->
      console.log data
      if data.count == 0
        $("#search-results-buffer").html("")
        $("#search-results").html("""<h3>No results...</h3><br><br>""")
        $("#search-spinner").hide()
        $("#search-results").show()

        pagination_html = paginationTemplate {pages: 0}

        $("#results-header")[0].scrollIntoView()
        $(".search-pagination").html pagination_html
        $("#results-header").text("#{data.count} Search Results")
      else
        _html = ""
        for result in data.results
          _html = _html + resultTemplate(result).replace("img", "i")

        $("#search-results-buffer").html(_html)
        $("#search-results-buffer").find("br").remove()
        $("#search-spinner").hide()
        $("#search-results").show()
        $("#search-results").html($("#search-results-buffer").html())
        $("#search-results-buffer").html("")

        # terms = $("#search-for").val().split(" ")
        # for term in terms
        #   term = term.trim()
        #   if term == ""
        #     continue
        #   term_re = new RegExp("(.*?>?.*)("+term+"?)(.*<?.*?)", "gi")
        #   $(".search-result-title").each () ->
        #     $(this).html($(this).html().replace(term_re, """$1<span style="background-color: yellow">"""+"$2"+"</span>$3"))
        #   $(".search-result-content p").each () ->
        #     $(this).html($(this).html().replace(term_re, """$1<span style="background-color: yellow">"""+"$2"+"</span>$3"))
        #   $(".search-result-content blockquote").each () ->
        #     $(this).html($(this).html().replace(term_re, """$1<span style="background-color: yellow">"""+"$2"+"</span>$3"))

        $(".search-result-content").dotdotdot({height: 200, after: ".readmore"})
        
        if $("#content-search").val() != "posts"
          pages = []
          max_pages = Math.ceil data.count/data.pagination
          if max_pages > 5
            if page > 3 and page < max_pages-5
              pages = [page-2..page+5]
            else if page > 3
              pages = [page-2..max_pages]
            else if page <= 3
              pages = [1..page+5]
          else
            pages = [1..Math.ceil data.count/data.pagination]
          pagination_html = paginationTemplate {pages: pages}
        else
          pagination_html = paginationForPostsHTMLTemplate

        $("#results-header")[0].scrollIntoView()
        $(".search-pagination").html pagination_html
        $(".search-pagination").show()
        if $("#content-search").val() != "posts"
          $("#results-header").text("#{data.count} Search Results")
        else
          $("#results-header").text("Search Results")
          if data.count == 20
            $(".next-page").hide()
            max_pages = page
          else
            $(".next-page").show()
            max_pages = page + 1
          console.log page
          if page == 1
            $(".previous-page").hide()
          else
            $(".previous-page").show()
          
        $(".page-link-#{page}").parent().addClass("active")

  $("#search").click (e) ->
    e.preventDefault()
    page = 1
    $(".search-pagination").hide()
    updateSearch()

  $("form").submit (e) ->
    e.preventDefault()
    $("#search").click()

  $(".search-pagination").delegate ".next-page", "click", (e) ->
    e.preventDefault()
    element = $(this)
    if page != max_pages
      $(".change-page").parent().removeClass("active")
      page++
      updateSearch()

  $(".search-pagination").delegate ".previous-page", "click", (e) ->
    e.preventDefault()
    element = $(this)
    if page != 1
      $(".change-page").parent().removeClass("active")
      page--
      updateSearch()

  $(".search-pagination").delegate ".go-to-end", "click", (e) ->
    e.preventDefault()
    element = $(this)
    page = parseInt(max_pages)
    updateSearch()

  $(".search-pagination").delegate ".change-page", "click", (e) ->
    e.preventDefault()
    element = $(this)
    page = parseInt(element.text())
    updateSearch()

  $(".search-pagination").delegate ".go-to-start", "click", (e) ->
    e.preventDefault()
    element = $(this)
    page = 1
    updateSearch()
