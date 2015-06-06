$ ->
  class Status
    constructor: () ->
      @id = $("#status").attr("data-id")
      do @refreshView
      
    addReply: () ->
      $.post "/status/#{@id}/", {text: $("#status-reply")[0].value, reply: true}, (response) =>
        $("#status-reply")[0].value = ""
        @refreshView(true)
    
    replyTMPL: (vars) ->
      return """
      <div class="status-reply" data-id="#{vars.pk}">  
        <img src="#{vars.user_avatar}" width="#{vars.user_avatar_x}px" height="#{vars.user_avatar_y}px">
        <p><a href="#">#{vars.user_name}</a><span class="status-mod-controls"></span>
        <br>#{vars.text}
        <br><span class="status-reply-time">#{vars.time}</span></p>
        <hr>
      </div>
      """
      
    refreshView: (scrolldown=false) ->
      $.get "/status/#{@id}/replies", {}, (response) =>
        $("#status-replies").html("")
        
        for comment in response.replies
          $("#status-replies").append @replyTMPL(comment)
        
        if scrolldown
          $("#status-replies").scrollTop($('#status-replies')[0].scrollHeight)
        
  window.status_ = new Status
    
  $("#submit-reply").click (e) ->
    e.preventDefault()
    do s.addReply 