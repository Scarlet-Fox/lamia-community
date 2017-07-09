$ ->
  other_editor = new InlineEditor("#character-other")
  other_editor.noSaveButton()
  
  window.onbeforeunload = () ->
    if not window.save
      return "You haven't saved your changes."
  
  $("form").submit (e) ->
    window.save = true
    $("#other").val(other_editor.getHTML())
    return true