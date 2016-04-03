$ ->
  window.onbeforeunload = () ->
     if not window.save
       return "You haven't saved your changes."
       
  class NewTopic
    constructor: (slug) ->
      @slug = slug
      @inline_editor = new InlineEditor "#new-post-box", "", false
      @meta = {}
      @poll = {}
      new_topic = self

      @inline_editor.onSave (html, text) ->
        title = $("#title").val()
        prefix = $("#prefix").val()
        meta = new_topic.meta
        poll = new_topic.poll
        $.post "/category/#{slug}/new-topic", JSON.stringify({html: html, text: text, meta: meta, title: title, prefix: prefix, poll: poll}), (data) =>
          if data.error?
            topic.inline_editor.flashError data.error
          else
            window.location = data.url

  window.topic = new NewTopic($("#new-topic-form").data("slug"))
