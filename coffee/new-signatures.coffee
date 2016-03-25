$ ->
  blog_entry_editor = new InlineEditor("#sig-html")
  blog_entry_editor.noSaveButton()

  window.onbeforeunload = () ->
     if not window.save
       return "You haven't saved your changes."

   $("form").submit (e) ->
     window.save = true
     $("#html").val(blog_entry_editor.quill.getHTML())
     return true
