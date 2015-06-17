$ ->
  class Dashboard
    constructor: () ->
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
      
    addToPanel: (notification) ->
      category_element = $("#notifs-"+notification.category)
      if category_element.length == 0
        panel = 
          panel_id: notification.category
          panel_title: @category_names[notification.category]
        @dashboard_container.append(@panelTemplate(panel))
        category_element = $("#notifs-"+notification.category)
      
      category_element.append(@notificationTemplate(notification))
      
    buildDashboard: () ->
      $.post "/dashboard/notifications", {}, (response) =>
        for notification in response.notifications
          @addToPanel notification
          
    notificationHTML: () ->
      return """
      <li class="list-group-item" id="{{_pk}}" data-stamp="{{stamp}}">
        <a href="{{url}}">{{text}}</a>
        <p class="text-muted"> by <a href="/members/{{member_name}}/">{{member_disp_name}}</a> - {{time}}</p>
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