$ ->
  # This code needs to be on the "other side" of the iframe
  # <script>
  #   (function() {
  #     window.addEventListener('message', function(event) {
  #       if(height = event.data['height']) {
  #         $('#lamia-inline').css('height', height + 'px')
  #       }
  #     })
  #   }).call(this);
  # </script>

  updateHeight = () ->
    height = $("body").height() + 100
    window.parent.postMessage
      height: height,
      "*"
      
  window.updateHeight = updateHeight
  
  $(window).on 'resize', updateHeight
  updateHeight()