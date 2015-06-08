$ ->
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