$ ->
  $.ajaxSetup
    cache: false
  
  if not window.my_tz?
    window.my_tz = "US/Pacific"
  
  $(".href_span").click (e) ->
    window.location = $(this).attr("href")
    
  $(".to-top").click (e) ->
    e.preventDefault()
    window.scrollTo 0, 0
  
  $(".sign-out").click (e) ->
    e.preventDefault()
    $.post "/sign-out", (data) ->
      window.location = "/"
  
  window.RegisterAttachmentContainer = (selector) ->
    imgModalHTML = () ->
      return """
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
            <h4 class="modal-title">Full Image?</h4>
          </div>
          <div class="modal-body">
            Would you like to view the full image? It is about <span id="img-click-modal-size"></span>KB in size.
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-primary" id="show-full-image">Yes</button>
            <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
          </div>
        </div>
      </div>
      """
      
    gifModalHTML = () ->
      return """
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
            <h4 class="modal-title">Play GIF?</h4>
          </div>
          <div class="modal-body">
            Would you like to play this gif image? It is about <span id="img-click-modal-size"></span>KB in size.
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-primary" id="show-full-image">Play</button>
            <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
          </div>
        </div>
      </div>
      """
    
    $(selector).delegate ".attachment-image", "click", (e) ->
      e.preventDefault()
      element = $(this)
      if element.data("first_click") == "yes"
        element.attr("original_src", element.attr("src"))
        element.data("first_click", "no")
      element.attr("src", element.attr("original_src"))
      if element.data("show_box") == "no"
        return false
      url = element.data("url")
      extension = url.split(".")[url.split(".").length-1]
      size = element.data("size")
      $("#img-click-modal").modal('hide')
      if extension == "gif" and parseInt(size) > 1024
        $("#img-click-modal").html gifModalHTML()
        $("#img-click-modal").data("biggif", true)
        $("#img-click-modal").data("original_element", element)
        $("#img-click-modal-size").html(element.data("size"))
        $("#img-click-modal").modal('show')
      else
        $("#img-click-modal").html imgModalHTML()
        $("#img-click-modal").data("full_url", element.data("url"))
        $("#img-click-modal-size").html(element.data("size"))
        $("#img-click-modal").data("original_element", element)
        $("#img-click-modal").data("biggif", false)
        $("#img-click-modal").modal('show')
      
    $("#img-click-modal").delegate "#show-full-image", "click", (e) ->
      e.preventDefault()
      unless $("#img-click-modal").data("biggif")
        window.open($("#img-click-modal").data("full_url"), "_blank")
        $("#img-click-modal").modal('hide')
      else
        element = $("#img-click-modal").data("original_element")
        element.attr("src", element.attr("src").replace(".gif", ".animated.gif"))
        $("#img-click-modal").modal('hide')
  
  if window.logged_in
    socket = io.connect('http://' + document.domain + ':3000' + '')

  notificationHTML = """
      <li class="notification-li"><a href="{{url}}" data-notification="{{_id}}" class="notification-link dropdown-notif-{{_id}}-{{category}}">{{text}}</a></li>
      """
      
  notificationTemplate = Handlebars.compile(notificationHTML)
  
  if window.logged_in
    socket.emit "user", {user: window.woe_is_me}
    
    socket.on "notify", (data) ->
      if window.woe_is_me in data.users
        counter_element = $(".notification-counter")
        counter_element.text(data.count)
        counter_element.css("background-color", "#B22222")
        $(".dashboard-counter").text(data.dashboard_count)
      
        title_count = document.title.match(/\(\d+\)/)
        if title_count
          document.title = document.title.replace(title_count[0], "(#{data.count})")        
        else
          document.title = "(#{data.count}) - " + document.title
      
        if $($(".notification-dropdown")[0]).find(".notification-li").length > 14
          $(".notification-dropdown").each () ->
            $(this).find(".notification-li")[$(this).find(".notification-li").length-1].remove()
      
        if $($(".notification-dropdown")[0]).find(".notification-li").length == 0
          $(".notification-dropdown").each () ->
            $(this).append(notificationTemplate(data))
        else
          $(".notification-dropdown").each () ->
            $(this).find(".notification-li").first().before(notificationTemplate(data))
  
  $(".post-link").click (e) ->
    e.preventDefault()
    $.post $(this).attr("href"), (data) ->
      window.location = data.url

  $(".notification-dropdown").delegate ".notification-link", "click", (e) ->
    e.preventDefault()
    $.post "/dashboard/ack_notification", JSON.stringify({notification: $(this).data("notification")}), (data) =>
      window.location = $(this).attr("href")
      
  $(".notification-dropdown-toggle").click (e) ->
    $.post "/dashboard/mark_seen", (d) ->
      $(".notification-counter").text("0")
      $(".notification-counter").css("background-color", "#777")

  window.setupContent = () ->
    window.addExtraHTML("body")
  
  window.addExtraHTML = (selector) ->
    $(selector).find(".content-spoiler").before """
      <a class="btn btn-info btn-xs toggle-spoiler">Toggle Spoiler</a>
      """
      
    $(selector).find(".toggle-spoiler").click (e) ->
      spoiler = $(this).next(".content-spoiler")
      if spoiler.is(":visible")
        spoiler.hide()
      else
        spoiler.show()
    
    blockquote_attribution_html = """
      {{#if author}}<p>{{#if time}}On {{#if link}}<a href="{{link}}" target="_blank">{{time}}{{/if}}{{#if link}}</a>{{/if}}, {{/if}}{{#if authorlink}}<a href="{{authorlink}}" class="hover_user" target="_blank">{{/if}}<strong>{{author}}</strong>{{#if authorlink}}</a>{{/if}} said:</p>{{/if}}
    """
    blockquote_attribution_template = Handlebars.compile(blockquote_attribution_html)
    
    $(selector).find("blockquote").each () ->
      element = $(this)
      time = moment.unix(element.data("time")).tz(window.my_tz).format("MMMM Do YYYY @ h:mm:ss a")
      element.find("blockquote").remove()
      element.html(element.html().replace(new RegExp("<p>&nbsp;</p>", "g"), ""))
      element.dotdotdot({height: 100})
      if time != "Invalid date"
        element.prepend blockquote_attribution_template
          link: element.data("link")
          time: time
          author: element.data("author")
          authorlink: element.data("authorlink")
      else
        element.prepend blockquote_attribution_template
          link: element.data("link")
          time: false
          author: element.data("author")
          authorlink: element.data("authorlink")
        
  $("#new-status").click (e) ->
    e.preventDefault()
    $.post "/create-status", JSON.stringify({message: $("#status-new").val()}), (data) ->
      if data.error?
        $("#create-status-error").remove()
        $("#status-new").parent().prepend """
          <div class="alert alert-danger alert-dismissible fade in" role="alert" id="create-status-error">
            <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">×</span></button>
            #{data.error}
          </div>
          """
      else
        window.location = data.url
  
  p_html = """
    <div class="media-left">
      <a href="/member/{{login_name}}"><img src="{{avatar_image}}" height="{{avatar_y}}" width="{{avatar_x}}"></a>
    </div>
    <div class="media-body">
      <table class="table">
        <tbody>
        <tr>
          <th style="width: 130px;">Group</th>
          <td><span style="color:#F88379;"><strong>Members</strong></span><br></td>
        </tr>
        <tr>
          <th>Joined</th>
          <td>{{joined}}</td>
        </tr>
        <tr>
          <th>Login Name</th>
          <td>{{login_name}}</td>
        </tr>
        <tr>
          <th>Last Seen</th>
          <td>{{last_seen}}</td>
        </tr>
        {{#if last_seen_at}}
        <tr>
          <th>Last Seen At</th>
          <td><a href="{{last_seen_url}}">{{last_seen_at}}</a></td>
        </tr>
        {{/if}}
        {{#if roles}}
        <tr>
          <th>Roles</th>
          <td>
          {{#each roles}}
            <b>{{{this}}}</b>{{#unless @last}}, {{/unless}}
          {{/each}}
        </tr>
        {{/if}}
        </tbody>
      </table>
    </div>
  """
  hoverTemplate = Handlebars.compile(p_html)
  
  window.hover_cache = {}
  $(document).on "mouseover", ".hover_user", (e) ->
    e.preventDefault()
    element = $(this)
    
    timeout = setTimeout () ->
      user = element.attr("href").split("/").slice(-1)[0]
      placement = "bottom"
      if element.data("hplacement")?
        placement = element.data("hplacement")
    
      if window.hover_cache[user]?
        data = window.hover_cache[user]
        _html = hoverTemplate(data)
        element.popover
          html: true
          container: 'body'
          title: data.name
          content: _html
          placement: placement
        element.popover("show")
        checkAndClear = (n=100) ->
          setTimeout () ->
            if $(".popover:hover").length != 0
              do checkAndClear
            else
              element.popover("hide")
          , n
        checkAndClear(2000)
      else
        $.post "/get-user-info-api", JSON.stringify({user: user}), (data) ->
          window.hover_cache[user] = data
          _html = hoverTemplate(data)
          element.popover
            html: true
            content: _html
            container: 'body'
            title: data.name
            placement: placement
          element.popover("show")
          checkAndClear = (n=100) ->
            setTimeout () ->
              if $(".popover:hover").length != 0
                do checkAndClear
              else
                element.popover("hide")
            , n
          checkAndClear(2000)
    , 1000
    element.data("timeout", timeout)
    
  $(document).on "mouseout", ".hover_user", (e) ->
    e.preventDefault()
    element = $(this)
    clearTimeout element.data("timeout")
    
  reportModalHTML = () ->
    return """
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
          <h4 class="modal-title">Report Content</h4>
        </div>
        <div class="modal-body">
          Ready to make a report? Supply a reason and click submit.
          <br><br>
          <input class="form-control report-reason" style="width: 400px; max-width: 100%;">
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-danger" id="modal-submit-report">Report</button>
          <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
        </div>
      </div>
    </div>
    """
  
  $(document).on "click", ".report-button", (e) ->
    element = $(this)
    $("#report-click-modal").html reportModalHTML()
    $("#report-click-modal").data("pk", element.data("pk"))
    $("#report-click-modal").data("type", element.data("type"))
    
    $("#modal-submit-report").click (e) ->
      post_data = 
        pk: $("#report-click-modal").data("pk")
        content_type: $("#report-click-modal").data("type")
        reason: $(".report-reason").val()
      $.post "/make-report", JSON.stringify(post_data), (data) ->
        $("#report-click-modal").modal("hide")
        element.text("Report Submitted")
        element.addClass("btn-success")
        element.addClass("disabled")
    
    $("#report-click-modal").modal("show")
    
    
  
    
  
  return