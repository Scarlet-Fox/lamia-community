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
      
      # if content_type == "posts"
      # else if content_type == "topics"
      # else if content_type == "status"
      # else if content_type == "messages"
      