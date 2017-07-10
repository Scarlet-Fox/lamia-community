$ ->
  $(".notification-toggle").click (e) ->
    element = $(this)
    category = element.data("target")
    method = element.data("method")
    on_or_off = element.is(":checked")

    _data =
      category: category
      method: method
      on_or_off: on_or_off

    $.post "/member/#{window.l_name}/toggle-notification-method", JSON.stringify(_data), (data) =>
      console.log data

  $("#add-user-field").click (e) ->
    e.preventDefault()
    field_box = $($(".fields")[0])
    field = $("#user-field-select").val()
    value = $("#user-field-value").val()

    if not field_box.is(":visible")
      field_box.show()

    field_box.children("ul").append """<li><strong>#{field}</strong>&nbsp;&nbsp;&nbsp;#{value}</li>"""

    $.post "/member/#{window.l_name}/add-user-field", JSON.stringify({field: field, value: value}), (data) =>
      console.log

  $(".remove-user-field").click (e) ->
    e.preventDefault()

    element = $(this)
    field = element.data("field")
    value = element.data("value")

    element.parent().remove()

    $.post "/member/#{window.l_name}/remove-user-field", JSON.stringify({field: field, value: value}), (data) =>
      console.log

  $("#user-ignore-select").select2
    ajax:
      url: "/user-list-api",
      dataType: 'json',
      delay: 250,
      data: (params) ->
        return {
          q: params.term
        }
      processResults: (data, page) ->
        console.log {
          results: data.results
        }
        return {
          results: data.results
        }
      cache: true
    minimumInputLength: 2

  $("#birthday").datepicker
    format: "m/d/yyyy"
    clearBtn: true

  $("#user-ignore-button").click (e) ->
    e.preventDefault()
    data = $("#user-ignore-select").val()

    $.post "/member/#{window.l_name}/ignore-users", JSON.stringify({data: data}), (data) =>
      window.location = data.url
