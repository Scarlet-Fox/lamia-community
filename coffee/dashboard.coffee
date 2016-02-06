$ ->
  class Dashboard
    constructor: () ->
      $grid = $('#dashboard-container');
      window.grid = $grid
      $grid.shuffle
        speed: 0
        
      @categories = {}
      @notificationTemplate = Handlebars.compile(@notificationHTML())
      @panelTemplate = Handlebars.compile(@panelHTML())
      @dashboard_container = $("#dashboard-container")
      
      @category_names = 
        topic: "Topics"
        pm: "Private Messages"
        mention: "Mentioned"
        topic_reply: "Topic Replies"
        boop: "Boops"
        mod: "Moderation"
        status: "Status Updates"
        new_member: "New Members"
        announcement: "Announcements"
        profile_comment: "Profile Comments"
        rules_updated: "Rule Update"
        faqs: "FAQs Updated"
        user_activity: "Followed:User Activity"
        streaming: "Streaming"
        other: "Other"
      
      do @buildDashboard
      
      _panel=this
      
      socket = io.connect('http://' + document.domain + ':3000' + '')
      
      socket.on "notify", (data) ->
        if window.woe_is_me in data.users
          $(".nothing-new").remove()
          _panel.addToPanel(data, true)
          do _panel.setPanelDates
          
      $("#dashboard-container").on 'removed.shuffle', (e) =>
        do @isPanelEmpty
      
      $("#dashboard-container").delegate ".ack_all", "click", (e) ->
        e.preventDefault()
        panel = $("#"+$(this).data("panel"))
        $.post "/dashboard/ack_category", JSON.stringify({category: panel.attr("id")}), (data) =>
          if data.success?
            $(".dashboard-counter").text(data.count)
            $("#dashboard-container").shuffle("remove", panel)
      
      $("#dashboard-container").delegate ".ack_single_href", "click", (e) ->
        e.preventDefault()
        $.post "/dashboard/ack_notification", JSON.stringify({notification: $(this).data("notification")}), (data) =>
          window.location = $(this).attr("href")
      
      $("#dashboard-container").delegate ".ack_single", "click", (e) ->
        e.preventDefault()
        notification = $("#"+$(this).data("notification"))
        panel_notifs = $("#notifs-"+$(this).data("panel"))
        panel = $("#"+$(this).data("panel"))
        $.post "/dashboard/ack_notification", JSON.stringify({notification: notification.attr("id")}), (data) =>
          if data.success?
            $(".dashboard-counter").text(data.count)
            if panel_notifs.children().length < 2
              $("#dashboard-container").shuffle("remove", panel)
            else
              notification.remove()
              
    isPanelEmpty: () ->
      if $(".dashboard-panel").length == 0
        $("#dashboard-container").before """
        <p class="nothing-new">No new notifications, yet.</p>
        """
      else
        $(".nothing-new").remove()
        
    setPanelDates: () ->
      $(".dashboard-panel").children(".panel").children("ul").each () ->
        element = $(this)
        first_timestamp = element.children("li").first().data("stamp")
        element.parent().parent().data("stamp", first_timestamp )
      setTimeout () ->
        $("#dashboard-container").shuffle('appended', $(".dashboard-panel"))
        $("#dashboard-container").shuffle("update")
        sort_opts = 
          reverse: true
          by: (el) ->
            return el.data("stamp")
        $("#dashboard-container").shuffle("sort", sort_opts)
      , 100
    
    addToPanel: (notification, live=false) ->
      category_element = $("#notifs-"+notification.category)
      if category_element.length == 0
        panel = 
          panel_id: notification.category
          panel_title: @category_names[notification.category]
        @dashboard_container.append(@panelTemplate(panel))
        category_element = $("#notifs-"+notification.category)
      
      if not live
        if notification.content?._ref?
          notification.reference = notification.content._ref
        else
          notification.reference = ""
          
      notification._member_name = notification.member_pk
      
      existing_notification = $(".ref-#{notification.reference}-#{notification.category}-#{notification._member_name}")
      if existing_notification.length > 0 and notification.reference != ""
        count = parseInt(existing_notification.data("count"))
        count = count + 1
        if not existing_notification.children("media-left").is(":visible")
          existing_notification.children(".media-left").show()
        existing_notification.data("count", count)
        existing_notification.data("stamp", notification.stamp)
        existing_notification.children(".media-left").children(".badge").text(count)
        existing_notification.find(".m-name").attr("href", "/member/#{notification.member_name}")
        existing_notification.find(".m-name").text(notification.member_disp_name)
        existing_notification.find(".m-time").text(notification.time)
        existing_notification.find(".m-title").text(notification.text)
        existing_notification.find(".m-title").attr("href", notification.url)
        if live
          if existing_notification[0] != category_element.children().first()[0]
            category_element.prepend(existing_notification)
      else
        if live
          category_element.prepend(@notificationTemplate(notification))
        else
          category_element.append(@notificationTemplate(notification))
      
    buildDashboard: () ->
      $.post "/dashboard/notifications", {}, (response) =>
        for notification in response.notifications
          @addToPanel notification
        do @isPanelEmpty
        do @setPanelDates
      
    notificationHTML: () ->
      return """
      <li class="list-group-item ref-{{reference}}-{{category}}-{{_member_name}}" id="{{_id}}" data-stamp="{{stamp}}" data-count="1">
        <div class="media-left" style="display: none;"><span class="badge"></span></div>
        <div class="media-body">
          <a href="{{url}}" data-notification="{{_id}}" class="m-title ack_single_href">{{text}}</a><button class="close ack_single" data-notification="{{_id}}" data-panel="{{category}}">&times;</button>
          <p class="text-muted"> by <a href="/member/{{member_name}}" class="m-name hover_user">{{member_disp_name}}</a> - <span class="m-time">{{time}}</span></p>
        </div>
      </li>
      """
      
    panelHTML: () ->
      return """
      <div class="col-sm-6 col-md-4 dashboard-panel" id="{{panel_id}}">
        <div class="panel panel-default">
          <div class="panel-heading">
            <span>{{panel_title}}</span>
            <button class="close ack_all" data-panel="{{panel_id}}">&times;</button>
          </div>
          <ul class="list-group panel-body" id="notifs-{{panel_id}}">
          </ul>
        </div>
      </div>
      """
      
  window.woeDashboard = new Dashboard