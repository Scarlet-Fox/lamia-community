$ ->
  class NewTopic
    constructor: (slug) ->
      @slug = slug
      @inline_editor = new InlineEditor "#new-post-box", "", false
      
      
  window.topic = new NewTopic($("#new-topic-form").data("slug"))