$ ->
  class NewTopic
    constructor: () ->
      @inline_editor = new InlineEditor "#new-post-box", "", false
      new_topic = self
      
      $("#to").select2
        ajax:
          url: "/user-list-api",
          dataType: 'json',
          delay: 250,
          data: (params) ->
            return {
              q: params.term
            }
          processResults: (data, page) ->
            console.log {
              results: data.results
            }
            return {
              results: data.results
            }
          cache: true
        minimumInputLength: 2
      
      @inline_editor.onSave (html, text) ->
        title = $("#title").val()
        prefix = $("#prefix").val()
        to = $("#to").val()
        $.post "/new-message", JSON.stringify({html: html, text: text, title: title, prefix: prefix, to: to}), (data) =>
          if data.error?
            topic.inline_editor.flashError data.error
          else
            window.location = data.url
      
  window.topic = new NewTopic()