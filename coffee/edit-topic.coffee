$ ->
  class EditTopic
    constructor: (slug) ->
      @slug = slug
      @inline_editor = new InlineEditor "#new-post-box", "", true, true
      @meta = {}
      @poll = {}
      edit_topic= self
      
      @inline_editor.onSave (html, text, edit_reason) ->
        title = $("#title").val()
        prefix = $("#prefix").val()
        meta = edit_topic.meta
        poll = edit_topic.poll
        $.post "/t/#{slug}/edit-topic", JSON.stringify({html: html, text: text, meta: meta, title: title, prefix: prefix, poll: poll, edit_reason: edit_reason}), (data) =>
          console.log data
          if data.error?
            topic.inline_editor.flashError data.error
          else
            window.location = "/t/#{slug}"
            
      @inline_editor.onCancel (html, text) ->
        window.location = "/t/#{slug}"
        
      
  window.topic = new EditTopic($("#edit-topic-form").data("slug"))