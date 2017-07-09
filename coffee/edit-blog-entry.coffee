$ ->
  blog_entry_editor = new InlineEditor("#blog-entry")
  blog_entry_editor.noSaveButton()

  window.onbeforeunload = () ->
     if not window.save
       return "You haven't saved your changes."

   $("form").submit (e) ->
     window.save = true
     $("#entry").val(blog_entry_editor.getHTML())
     return true
