$ ->
  class Dashboard
    constructor: () ->
      do @buildDashboard
      
    buildDashboard: () ->
      $.post "/dashboard/notifications", {}, (response) =>
        console.log response
        
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