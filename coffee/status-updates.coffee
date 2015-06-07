$ ->
  class Status
    constructor: () ->
      @id = $("#status").attr("data-id")
      @max_length = 250
      status = this
      @replyHTML = Handlebars.compile(@replyHTMLTemplate())
      do @refreshView
      
      @socket = io.connect('http://' + document.domain + ':3000' + '');
      
      @socket.on "connect", () =>
        @socket.emit 'join', "status--#{@id}"
      
      @socket.on "console", (data) ->
        console.log data
        
      @socket.on "event", (data) ->
        if data.reply?
          status.updateReplyCount data.count
          $("#status-replies").append status.replyHTML(data.reply)
          $("#status-replies").scrollTop($('#status-replies')[0].scrollHeight)
    
      $("#submit-reply").click (e) ->
        e.preventDefault()
        do status.addReply
        
      $("#status-reply").bind "propertychange change click keyup input paste", (e) ->
        status.updateCount $("#status-reply").val().length
      
    addReply: () ->
      $.post "/status/#{@id}/reply", JSON.stringify({reply: $("#status-reply").val()}), (data) =>
        if data.error?
          @flashError data.error
        else
          $("#status-reply").val("")
          @socket.emit "event", 
            room: "status--#{@id}"
            reply: data.newest_reply
            count: data.count
          
          @updateReplyCount data.count
          $("#status-replies").append @replyHTML(data.newest_reply)
          $("#status-replies").scrollTop($('#status-replies')[0].scrollHeight)
        
    flashError: (error) ->
      $(".status-reply-form").children(".alert").remove()
      $(".status-reply-form").prepend """<div class="alert alert-danger alert-dismissible fade in" role="alert">
                <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">×</span></button>
                #{error}
              </div>"""
    
    updateReplyCount: (c) ->
      if c > 99
        @flashError "This status update is full."
        $("#submit-reply").addClass "disabled"
      $("#status-status").text "Status Update - #{c} / 100 Replies"
    
    updateCount: (c) ->
      n = parseInt(c)
      c =  parseInt( n / @max_length * 100)
      
      style = "progress-bar-info"
      if c > 80
        style = "progress-bar-danger"
      else if c > 40
        style = "progress-bar-warning"

      $("#status-comment-count").html """
        <br><br>
        <div class="progress" style="width: 79%;">
          <div class="progress-bar #{style }" role="progressbar" aria-valuenow="#{c}" aria-valuemin="0" aria-valuemax="100" style="width: #{c}%;">
            <span class="sr-only">#{c}%</span>
            #{n} / #{@max_length}
          </div>
        </div>"""
    
    replyHTMLTemplate: () ->
      return """
      {{#unless hidden}}
      <div class="status-reply" data-id="{{idx}}">
        <div class="media-left">
          <img src="{{user_avatar}}" width="{{user_avatar_x}}px" height="{{user_avatar_y}}px">
        </div>
        <div class="media-body">
          <p><a href="#">{{user_name}}</a><span class="status-mod-controls"></span>
          <br>{{{text}}}
          <br><span class="status-reply-time">{{time}}</span></p>
        </div>
        <hr>
      </div>
      {{/unless}}
      """
      
    refreshView: (scrolldown=false) ->
      $.get "/status/#{@id}/replies", {}, (response) =>
        $("#status-replies").html("")
        
        @updateReplyCount response.count
        
        for comment in response.replies
          $("#status-replies").append @replyHTML(comment)
                  
        if scrolldown
          $("#status-replies").scrollTop($('#status-replies')[0].scrollHeight)
        
  window.status_ = new Status()