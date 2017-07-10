$ ->
  window.addExtraHTML(".list-group-item")

  $(".boop-link").click (e) ->
    e.preventDefault()
    element = $(this)
    current_status = element.data("status")
    count = parseInt(element.data("count"))

    $.post element.attr("href"), JSON.stringify({}), (data) ->
      if current_status == "notbooped"
        element.children(".boop-text").text("Boop!")
        element.children(".badge").text("")
        element.data("status", "booped")
        element.data("count", count+1)
      else
        element.children(".boop-text").html("")
        element.data("status", "notbooped")
        element.children(".boop-text").text(" Boop")
        element.data("count", count-1)
        element.children(".badge").text(element.data("count"))
        element.children(".badge").css("background-color", "#555")

  if $("#new-post-box").length > 0
    inline_editor = new InlineEditor "#new-post-box", "", false, false, 150

    inline_editor.onSave (html, text) ->
      inline_editor.disableSaveButton()
      $.post $("#entry-url").attr("href")+"/new-comment", JSON.stringify({post: html, text: text}), (data) =>
        if data.no_content?
          inline_editor.flashError "You forgot to write something."
        if data.error?
          inline_editor.flashError data.error

        if data.success?
          inline_editor.clearEditor()
          window.location = data.url
        else
          inline_editor.enableSaveButton()
