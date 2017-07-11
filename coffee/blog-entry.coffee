$ ->  
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
    
    getSelectionText = () ->
      text = ""
      if window.getSelection
        text = window.getSelection().toString();
      else if document.selection and document.selection.type != "Control"
        text = document.selection.createRange().text;
      return text
      
    $(".list-group-item").delegate ".reply-button", "click", (e) ->
      e.preventDefault()

      try
        post_object = getSelectionParentElement().closest(".post-content")
      catch
        post_object = null
      highlighted_text = getSelectionText().trim()

      element = $(this)
      my_content = ""
      
      if post_object? and post_object == $("#post-#{element.data("pk")}")[0]
        my_content = "[reply=#{element.data("pk")}:blogcomment:#{element.data("author")}]\n#{highlighted_text}\n[/reply]"
      else
        my_content = "[reply=#{element.data("pk")}:blogcomment:#{element.data("author")}]\n\n"

      x = window.scrollX
      y = window.scrollY
      try
        inline_editor.quill.focus()
      catch
        current_position = 0

      window.scrollTo x, y
      unless current_position?
        current_position = inline_editor.quill.getSelection(true).index
        unless current_position?
          current_position = inline_editor.quill.getLength()
      inline_editor.quill.insertText current_position, my_content
    

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
