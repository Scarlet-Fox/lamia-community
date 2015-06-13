$ ->
  $(".variable-option").hide()
  $(".posts-option").show()
  page = 1
  
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
    else if content_type == "messages"
      $(".variable-option").hide()
      $(".messages-option").show()
      
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
  
  resultTemplateHTML = () ->
    return """
    <ul class="list-group">
      <li class="list-group-item">
        <p>
          <b>
            <a href="{{url}}">{{{title}}}</a>
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
        <p class="text-muted">by <a href="{{author_profile_link}}">{{author_name}}</a> - {{time}}
        </p>
      </li>
    </ul>
    """
  resultTemplate = Handlebars.compile(resultTemplateHTML())
            
  paginationHTMLTemplate = () ->
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
  paginationTemplate = Handlebars.compile(paginationHTMLTemplate())  
  
  updateSearch = () ->
    content_type = $("#content-search").val()
    
    data = 
      q: $("#search-for").val()
      content_type: content_type
      page: page
      
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
    
    $.post "/search", JSON.stringify(data), (data) ->
      _html = ""
      for result in data.results
        _html = _html + resultTemplate(result)
        
      $("#search-results").html(_html)
      $(".search-result-content img").hide()
      $(".search-result-content br").hide()
      $(".search-result-content").dotdotdot({height: 200, after: ".readmore"})
      
      terms = $("#search-for").val().split(" ")
      for term in terms
        term = term.trim()
        if term == ""
          continue
        term_re = new RegExp("(.*?>?.*)("+term+"?)(.*<?.*?)", "gi")
        $(".search-result-content p").each () ->
          $(this).html($(this).html().replace(term_re, """$1<span style="background-color: yellow">"""+"$2"+"</span>$3"))
        $(".search-result-content blockquote").each () ->
          $(this).html($(this).html().replace(term_re, """$1<span style="background-color: yellow">"""+"$2"+"</span>$3"))

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
      
      $(".search-pagination").html pagination_html
  
  $("#search").click (e) ->
    e.preventDefault()
    updateSearch()
    
    # if content_type == "posts"
    # else if content_type == "topics"
    # else if content_type == "status"
    # else if content_type == "messages"
      