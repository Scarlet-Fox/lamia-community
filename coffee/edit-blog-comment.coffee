$ ->
  blog_comment_editor = new InlineEditor("#blog-comment")
  blog_comment_editor.noSaveButton()

  window.onbeforeunload = () ->
     if not window.save
       return "You haven't saved your changes."

   $("form").submit (e) ->
     window.save = true
     $("#comment").val(blog_comment_editor.getHTML())
     return true
