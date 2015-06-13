$ ->
  $(".variable-option").hide()
  $(".posts-option").show()
  
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
            <p>
              {{{description}}}
              {{#if readmore}}
              <a href="{{url}}" class="readmore">
                <br><b>Read more »</b>
              </a>
              {{/if}}
            </p>
          </div>
          <p class="text-muted">by <a href="{{author_profile_link}}">{{author_name}}</a> - {{time}}
          </p>
        </li>
      </ul>
      """
    resultTemplate = Handlebars.compile(resultTemplateHTML())
    
    $("#search").click (e) ->
      e.preventDefault()
      
      content_type = $("#content-search").val()
      
      data = 
        q: $("#search-for").val()
        content_type: content_type
        
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
        $(".search-result-content").dotdotdot({height: 200, after: ".readmore"})
      
      # if content_type == "posts"
      # else if content_type == "topics"
      # else if content_type == "status"
      # else if content_type == "messages"
      