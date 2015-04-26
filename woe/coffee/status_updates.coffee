$ ->
  class Status
    constructor: () ->
      @id = $("#status").attr("data-id")
    
    addReply: () ->
      $.post "/status/#{@id}/", {text: $("#status-reply")[0].value}, (response) ->
        console.log response
        #$("#status-reply")[0].value = ""
    
  s = new Status
    
  $("#submit-reply").click (e) ->
    e.preventDefault()
    do s.addReply 