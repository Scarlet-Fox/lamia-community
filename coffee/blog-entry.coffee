$ ->
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
