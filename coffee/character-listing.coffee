$ ->
  $('#character-table').dataTable
    responsive: true
    processing: true
    serverSide: true
    order: [[ 0, "desc" ]]
    lengthMenu: [[25, 50, 75, 100], [25, 50, 75, 100]]
    pageLength: 25
    ajax: 
      url: "/character-list-api"