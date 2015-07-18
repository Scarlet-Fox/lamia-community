$ ->
  class Status
    constructor: () ->
      @id = $("#status").attr("data-id")
      @max_length = 250
      status = this
      @replyHTML = Handlebars.compile(@replyHTMLTemplate())
      @confirmModelHTML = Handlebars.compile(@confirmModelHTMLTemplate())
      do @refreshView
      
      $("#status-comment-count").html """
        <br><br>
        <div class="progress" style="width: 79%;">
          <div class="progress-bar progress-bar-info" id="status-character-count-bar" role="progressbar" style="width: 0%">
            <span id="status-character-count-text"></span>
          </div>
        </div>"""
      @progress_bar = $("#status-character-count-bar")
      @progress_text = $("#status-character-count-text")
      
      @socket = io.connect('http://' + document.domain + ':3000' + '');
      
      @socket.on "connect", () =>
        @socket.emit 'join', "status--#{@id}"
      
      @socket.on "console", (data) ->
        console.log data
        
      @socket.on "event", (data) ->
        if data.reply?
          status.updateReplyCount data.count
          if ($("#status-replies").scrollTop() + $("#status-replies").innerHeight()) == $("#status-replies")[0].scrollHeight
            $("#status-replies").append status.replyHTML(data.reply)
            $("#status-replies").scrollTop($('#status-replies')[0].scrollHeight)
          else
            $("#status-replies").append status.replyHTML(data.reply)
    
      $("#submit-reply").click (e) ->
        e.preventDefault()
        do status.addReply
      
      $("#status-replies").delegate ".hide-reply", "click", (e) ->
        e.preventDefault()
        $("#confirm-hide-modal").modal('hide')
        $("#confirm-hide-modal").data("idx", $("#reply-"+$(this).attr("href")).data("idx"))
        $("#confirm-hide-modal").html status.confirmModelHTML({})
        $("#confirm-hide-modal").modal('show')
        
      $("#confirm-hide-modal").delegate "#confirm-hide", "click", (e) =>
        e.preventDefault()
        $("#confirm-hide-modal").modal('hide')
        reply_idx = $("#confirm-hide-modal").data("idx")
        $.post "/status/#{status.id}/hide-reply/#{reply_idx}", {}, (data) =>
          if data.success?
            $("#reply-"+reply_idx).remove()
      
      $("#status-reply").on "keyup", (e) ->
        status.updateCount $("#status-reply").val().length
      
    addReply: () ->
      $.post "/status/#{@id}/reply", JSON.stringify({reply: $("#status-reply").val()}), (data) =>
        if data.error?
          @flashError data.error
        else
          $(".status-reply-form").children(".alert").remove()
          $("#status-reply").val("")
          @socket.emit "event", 
            room: "status--#{@id}"
            reply: data.newest_reply
            count: data.count
          
          @updateReplyCount data.count
          @updateCount 0
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
      $("#status-status").text "#{c} / 100 Replies"
    
    updateCount: (c) ->
      n = parseInt(c)
      c =  parseInt( n / @max_length * 100)
      
      # style = "progress-bar-info"
      # if c > 80
      #   style = "progress-bar-danger"
      # else if c > 40
      #   style = "progress-bar-warning"
      
      @progress_bar.css("width", c+"%")
      @progress_text.text "#{n} / 250"

    replyHTMLTemplate: () ->
      return """
      {{#unless hidden}}
      <div class="status-reply" id="reply-{{idx}}" data-idx="{{idx}}">
        <div class="media-left">
          <a href="/member/{{author_login_name}}"><img src="{{user_avatar}}" width="{{user_avatar_x}}px" height="{{user_avatar_y}}px"></a>
        </div>
        <div class="media-body">
          <p><a href="/member/{{author_login_name}}" class="hover_user">{{user_name}}</a><span class="status-mod-controls">{{#if hide_enabled}}<a href="{{idx}}" class="inherit_colors hide-reply">(hide)</a>{{/if}}</span>
          <p>{{{text}}}</p>
          <span class="status-reply-time">{{time}}</span></p>
        </div>
        <hr>
      </div>
      {{/unless}}
      """
      
    confirmModelHTMLTemplate: () ->
      return """
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
            <h4 class="modal-title">Hide Reply?</h4>
          </div>
          <div class="modal-body">
            Are you sure you want to hide this reply?
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-primary" id="confirm-hide">Hide</button>
            <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
          </div>
        </div><!-- /.modal-content -->
      </div><!-- /.modal-dialog -->
      """
      
    refreshView: (scrolldown=false) ->
      $.get "/status/#{@id}/replies", {}, (response) =>
        $("#status-replies").html("")
        
        @updateReplyCount response.count
        
        for comment in response.replies
          comment.hide_enabled = true
          $("#status-replies").append @replyHTML(comment)
                  
        if scrolldown
          $("#status-replies").scrollTop($('#status-replies')[0].scrollHeight)
        
        if $("#status").data("locked") == "True"
          @flashError "This status update is locked."
          $("#submit-reply").addClass "disabled"
        
  window.status_ = new Status()
