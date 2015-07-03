$ ->
  appearance_editor = new InlineEditor("#character-appearance")
  appearance_editor.noSaveButton()
  personality_editor = new InlineEditor("#character-personality")
  personality_editor.noSaveButton()
  backstory_editor = new InlineEditor("#character-backstory")
  backstory_editor.noSaveButton()
  other_editor = new InlineEditor("#character-other")
  other_editor.noSaveButton()
  
  $("form").submit (e) ->
    $("#appearance").val(appearance_editor.quill.getHTML())
    $("#personality").val(personality_editor.quill.getHTML())
    $("#backstory").val(backstory_editor.quill.getHTML())
    $("#other").val(other_editor.quill.getHTML())
    return true