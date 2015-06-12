$ ->
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