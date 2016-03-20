$ ->
  if $("#new-post-box").length > 0
    @inline_editor = new InlineEditor "#new-post-box", "", false, false, 100

    @inline_editor.onSave (html, text) ->
      topic.inline_editor.disableSaveButton()
      # $.post "/t/#{topic.slug}/new-post", JSON.stringify({post: html, text: text, character: topic.selected_character, avatar: $("#avatar-picker-#{topic.inline_editor.quillID}").val()}), (data) =>

      # $.post "/t/#{topic.slug}/new-post", JSON.stringify({post: html, text: text, character: topic.selected_character, avatar: $("#avatar-picker-#{topic.inline_editor.quillID}").val()}), (data) =>
      #   topic.inline_editor.enableSaveButton()
      #   if data.closed_topic?
      #     topic.inline_editor.flashError "Topic Closed: #{data.closed_message}"
      #
      #   if data.no_content?
      #     topic.inline_editor.flashError "Your post has no text."
      #
      #   if data.error?
      #     topic.inline_editor.flashError data.error
      #
      #   if data.success?
      #     topic.inline_editor.clearEditor()
      #     socket.emit "event",
      #       room: "topic--#{topic.slug}"
      #       post: data.newest_post
      #       count: data.count
      #
      #     if topic.page == topic.max_pages
      #       data.newest_post.author_online = true
      #       data.newest_post.show_boop = true
      #       data.newest_post.can_boop = false
      #       data.newest_post._is_topic_mod = topic.is_mod
      #       data.newest_post._is_logged_in = topic.is_logged_in
      #       data.newest_post.author_login_name = window.woe_is_me
      #       data.newest_post._show_character_badge = not window.roleplay_area
      #       $("#post-container").append topic.postHTML data.newest_post
      #       window.addExtraHTML $("#post-"+data.newest_post._id)
      #     else
      #       window.location = "/t/#{topic.slug}/page/1/post/latest_post"
