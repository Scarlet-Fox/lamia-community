$ ->
  blog_description = new InlineEditor("#blog-description")
  blog_description.noSaveButton()

  window.onbeforeunload = () ->
     if not window.save
       return "You haven't saved your changes."

   $("form").submit (e) ->
     window.save = true
     $("#description").val(blog_description.quill.getHTML())
     return true
