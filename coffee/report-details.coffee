$ ->  
  if $("#new-comment-box").length > 0
    inline_editor = new InlineEditor "#new-comment-box", "", false, false, 150
    
    inline_editor.onSave (html, text) ->
      inline_editor.disableSaveButton()
      $.post "/admin/report/new-comment/"+$("#new-comment-box").attr("data-id"), JSON.stringify({post: html, text: text}), (data) =>
        if data.no_content?
          inline_editor.flashError "You forgot to write something."
        if data.error?
          inline_editor.flashError data.error

        if data.success?
          do location.reload()
        else
          inline_editor.enableSaveButton()
    