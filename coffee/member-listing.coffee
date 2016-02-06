$ ->
  $("#member-table").delegate ".toggle-show-roles-button", "click", (e) ->
    $(this).parent().children(".roles-div").toggle()  

  $('#member-table').dataTable
    responsive: true
    processing: true
    serverSide: true
    order: [[ 2, "desc" ]]
    lengthMenu: [[25, 50, 75, 100], [25, 50, 75, 100]]
    pageLength: 25
    columnDefs: [
      {
        targets: [1]
        iDataSort: 4
      },
      {
        targets: [2]
        iDataSort: 5
      },
      {
        targets: [4]
        visible: false
      },
      {
        targets: [5]
        visible: false
      }
    ]
    ajax: 
      url: "/member-list-api"