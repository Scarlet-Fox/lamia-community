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
    
    $(selector).delegate ".attachment-image", "click", (e) ->
      e.preventDefault()
      element = $(this)
      $("#img-click-modal").modal('hide')
      $("#img-click-modal").html imgModalHTML()
      $("#img-click-modal-preview").attr("src", element.attr("src"))
      url = $("#img-click-modal").data("full_url", element.data("url"))
      $("#img-click-modal-size").html(element.data("size"))
      $("#img-click-modal").modal('show')
      
    $("#img-click-modal").delegate "#show-full-image", "click", (e) ->
      e.preventDefault()
      window.open($("#img-click-modal").data("full_url"), "_blank")
      $("#img-click-modal").modal('hide')
      