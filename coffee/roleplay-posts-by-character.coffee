$ ->
  $("#post-table").delegate ".toggle-show-roles-button", "click", (e) ->
    $(this).parent().children(".roles-div").toggle()  

  $('#post-table').dataTable
    order: [[ 3, "desc" ]]
    lengthMenu: [[25, 50, 75, 100], [25, 50, 75, 100]]
    pageLength: 25
    columnDefs: [
      {
        targets: [2]
        iDataSort: 3
      },
      {
        targets: [3]
        visible: false
      }
    ]
    ajax: 
      url: window.location + "/character-post-list-api"