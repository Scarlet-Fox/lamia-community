$ ->
  class Status
    constructor: () ->
      @id = $("#status").attr("data-id")
      if $("#status").attr("data-mod") is "True"
        @mod = true
      else
        @mod = false
    
    addReply: () ->
      $.post "/status/#{@id}/", {text: $("#status-reply")[0].value, reply: true}, (response) =>
        $("#status-reply")[0].value = ""
        do @refreshView
    
    replyTMPL: (vars) ->
      return """
      <div class="status-reply" data-id="#{vars.pk}">  
        <img src="https://dl.dropboxusercontent.com/u/9060700/Commisions/Avatars/Key%20Gear%20-%20avatar.png" width="30px">
        <p><a href="#">#{vars.author}</a><span class="status-mod-controls"></span>
        <br>#{vars.text}
        <br><span class="status-reply-time">#{vars.date}</span></p>
        <hr>
      </div>
      """
      
    refreshView: () ->
      $.post "/status/#{@id}/", {}, (response) =>
        $("#status-replies").html("")
        
        for comment in response.replies
          $("#status-replies").append(@replyTMPL(comment))
        
        $("#status-replies").scrollTop($('#status-replies')[0].scrollHeight)
        
  s = new Status
  do s.refreshView
  
  makeInterval = (time, func)-> setInterval func, time
  
  makeInterval 3000, () ->
    do s.refreshView
    
  $("#submit-reply").click (e) ->
    e.preventDefault()
    do s.addReply 