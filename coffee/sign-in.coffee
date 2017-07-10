$ ->
  try
    if not navigator.userAgent.match(/iPhone/i)? and not navigator.userAgent.match(/iPad/i)?
      pl = navigator.plugins.length
      val = []
      for i in [0...pl]
        val.push(navigator.plugins[i])
    
      $("form").submit (e) ->
        # $('<input />').attr('type', 'hidden')
        #   .attr('name', "log_in_token")
        #   .attr('value', JSON.stringify({
        #     pl: val,
        #     sw: window.screen.width,
        #     cd: window.screen.colorDepth,
        #     sh: window.screen.height,
        #     tz:(new Date()).getTimezoneOffset()
        #   }))
        #   .appendTo('form')
        return true
  catch
    $("form").submit (e) ->
      $('<input />').attr('type', 'hidden')
        .attr('name', "log_in_token")
        .attr('value', JSON.stringify({}))
        .appendTo('form')
      return true
    