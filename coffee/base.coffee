$ ->
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
        $("#img-click-modal").modal('show')
        $("#img-click-modal").data("biggif", false)
      
    $("#img-click-modal").delegate "#show-full-image", "click", (e) ->
      e.preventDefault()
      unless $("#img-click-modal").data("biggif")
        window.open($("#img-click-modal").data("full_url"), "_blank")
        $("#img-click-modal").modal('hide')
      else
        element = $("#img-click-modal").data("original_element")
        element.attr("src", element.attr("src").replace(".gif", ".animated.gif"))
        $("#img-click-modal").modal('hide')
  
  socket = io.connect('http://' + document.domain + ':3000' + '')
  
  socket.on "notify", (data) ->
    if window.woe_is_me in data.users
      counter_element = $(".notification-counter")
      count = parseInt(counter_element.text())+1
      counter_element.text(count)
      window_title_count = document.title.split(" - ")[0]
      document.title = document.title.replace(window_title_count, "(#{count})")
      notification_listing = $("#notification-listing")
      notifications_listed = $("a.notification-link")
      if notifications_listed.length > 14
        notifications_listed[notifications_listed.length-1].remove()
        
      _html = """
      <a href="#{data.url}" data-notification="#{data._id}" class="notification-link dropdown-notif-#{data._id}-#{data.category}">#{data.text}</a>
      """
      
      if notifications_listed.length == 0
        $("#notification-dropdown").append(_html)
      else
        if notification_listing.find("dropdown-notif-#{data.id}-#{data.category}").length  == 0
          $(notifications_listed[0]).before(_html)
  
  $(".post-link").click (e) ->
    e.preventDefault()
    $.post $(this).attr("href"), (data) ->
      window.location = data.url

  $("#notification-dropdown").delegate ".notification-link", "click", (e) ->
    e.preventDefault()
    $.post "/dashboard/ack_notification", JSON.stringify({notification: $(this).data("notification")}), (data) =>
      window.location = $(this).attr("href")

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
      <p>On {{#if link}}<a href="{{link}}" target="_blank">{{/if}}{{time}}{{#if link}}</a>{{/if}}, {{#if authorlink}}<a href="{{authorlink}}" class="hover_user" target="_blank">{{/if}}{{author}}{{#if authorlink}}</a>{{/if}} said:</p>
    """
    blockquote_attribution_template = Handlebars.compile(blockquote_attribution_html)
    
    $(selector).find("blockquote").each () ->
      element = $(this)
      time = moment.unix(element.data("time")).format("MMMM Do YYYY @ h:mm:ss a")
      element.find("blockquote").remove()
      element.html(element.html().replace(new RegExp("<p>&nbsp;</p>", "g"), ""))
      element.dotdotdot({height: 100})
      if time != "Invalid date"
        element.prepend blockquote_attribution_template
          link: element.data("link")
          time: time
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
          <th>Group</th>
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
        </tbody>
      </table>
    </div>
  """
  hoverTemplate = Handlebars.compile(p_html)
  
  window.hover_cache = {}
  $(document).on "mouseover", ".hover_user", (e) ->
    e.preventDefault()
    element = $(this)
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
      
  # .popover
  #   trigger: "hover"
  #   html: true
  #   container: 'body'
  #   delay:
  #     show: 500
  #     hide: 100000
  #   content: () ->
  #     element = $(this)
  #
  #
  #
  #       _html = hoverTemplate(data)
  #       console.log _html
  #       return _html
      
      
  return