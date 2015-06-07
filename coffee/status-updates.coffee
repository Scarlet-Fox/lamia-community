$ ->
  class Status
    constructor: () ->
      @id = $("#status").attr("data-id")
      status = this
      @replyHTML = Handlebars.compile(@replyHTMLTemplate())
      do @refreshView
    
      $("#submit-reply").click (e) ->
        e.preventDefault()
        do status.addReply 
      
    addReply: () ->
      $.post "/status/#{@id}/reply", JSON.stringify({reply: $("#status-reply").val()}), (data) =>
        $("#status-reply").val("")
        @refreshView(true)
    
    replyHTMLTemplate: () ->
      return """
      <div class="status-reply" data-id="{{pk}}">
        <div class="media-left">
          <img src="{{user_avatar}}" width="{{user_avatar_x}}px" height="{{user_avatar_y}}px">
        </div>
        <div class="media-body">
          <p><a href="#">{{user_name}}</a><span class="status-mod-controls"></span>
          <br>{{text}}
          <br><span class="status-reply-time">{{time}}</span></p>
        </div>
        <hr>
      </div>
      """
      
    refreshView: (scrolldown=false) ->
      $.get "/status/#{@id}/replies", {}, (response) =>
        $("#status-replies").html("")
        
        for comment in response.replies
          $("#status-replies").append @replyHTML(comment)
        
        if scrolldown
          $("#status-replies").scrollTop($('#status-replies')[0].scrollHeight)
        
  window.status_ = new Status()