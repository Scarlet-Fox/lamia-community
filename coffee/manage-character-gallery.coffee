$ -> 
  Dropzone.autoDiscover = false
  $(".dropzone").dropzone
    url: window.location+"/attach"
    dictDefaultMessage: "Click here or drop a file in to upload (image files only)."
    acceptedFiles: "image/jpeg,image/jpg,image/png,image/gif"
    maxFilesize: 30
    init: () ->
      this.on "success", (file, response) ->
        window.location = window.location
        
  $(".save-button").click (e) ->
    element = $(this)
    element.addClass "disabled"
    pk = element.parent().parent().data("image")
    data = 
      pk: pk
      caption: element.parent().parent().find(".caption-for").val()
      source: element.parent().parent().find(".source-of").val()
      author: element.parent().parent().find(".created-by").val()
    $.post window.location+"/edit-image", JSON.stringify(data), (data) ->
      element.removeClass "disabled"
      
  $(".toggle-default-avatar-button").click (e) ->
    element = $(this)
    $(".toggle-default-avatar-button").removeClass("btn-success")
    $(".toggle-default-avatar-button").removeClass("disabled")
    $(".toggle-default-avatar-button").text("Make Default Avatar")
    element.addClass("btn-success")
    element.addClass("disabled")
    element.text("Default Avatar")
    data = 
      pk: element.parent().parent().data("image")
    $.post window.location+"/make-default-avatar", JSON.stringify(data), (data) ->
      
  $(".toggle-default-profile-button").click (e) ->
    element = $(this)
    $(".toggle-default-profile-button").removeClass("btn-success")
    $(".toggle-default-profile-button").removeClass("disabled")
    $(".toggle-default-profile-button").text("Make Default Profile Image")
    element.addClass("btn-success")
    element.addClass("disabled")
    element.text("Default Profile Image")
    data = 
      pk: element.parent().parent().data("image")
    $.post window.location+"/make-default-profile", JSON.stringify(data), (data) ->
      