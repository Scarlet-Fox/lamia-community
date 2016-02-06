$ ->
  $("#character-table").delegate ".toggle-show-roles-button", "click", (e) ->
    $(this).parent().children(".roles-div").toggle()  

  $('#character-table').dataTable
    responsive: true
    processing: true
    serverSide: true
    order: [[ 3, "desc" ]]
    lengthMenu: [[25, 50, 75, 100], [25, 50, 75, 100]]
    pageLength: 25
    ajax: 
      url: "/character-list-api"