$ ->
  class Topic
    constructor: (slug) ->
      @first_load = true
      @slug = slug
      topic = @
      @page = window._initial_page
      @max_pages = 1
      @pagination = window._pagination
      @postHTML = Handlebars.compile(@postHTMLTemplate())
      @paginationHTML = Handlebars.compile(@paginationHTMLTemplate())
      @is_mod = window._is_topic_mod
      if @is_mod == 0
        @is_mod = false
      else
        @is_mod = true
      @is_logged_in = window._is_logged_in
      @selected_character = ""
      @selected_avatar = ""

      if $(".io-class").data("path") != "/"
        socket = io.connect($(".io-class").data("config"), {path: $(".io-class").data("path")+"/socket.io"})
      else
        socket = io.connect($(".io-class").data("config"))

      window.onbeforeunload = () ->
        if topic.inline_editor.quill.getText().trim() != ""
          return "It looks like you were typing up a post."

      socket.on "connect", () =>
        socket.emit 'join', "topic--#{@slug}"

      socket.on "console", (data) ->
        console.log data

      socket.on "event", (data) ->
        if data.post?
          if topic.page == topic.max_pages
            data.post._is_topic_mod = topic.is_mod
            data.post._is_logged_in = topic.is_logged_in
            data.post.show_boop = true
            if data.post.author_login_name == window.woe_is_me
              data.post.can_boop = false
            else
              data.post.can_boop = true
            data.post._show_character_badge = not window.roleplay_area
            data.post.is_author = false
            $("#post-container").append topic.postHTML data.post
            window.addExtraHTML $("#post-"+data.post._id)
            if topic.inline_editor?
              if topic.inline_editor.quill.getText().trim() != "" and $("#new-post-box").find(".ql-editor").is(":focus")
                $("#new-post-box")[0].scrollIntoView()
          else
            topic.max_pages = Math.ceil data.count/topic.pagination
            topic.page = topic.max_pages

      window.socket = socket

      do @refreshPosts

      if window._can_edit? and $("#new-post-box").length > 0
        @inline_editor = new InlineEditor "#new-post-box", "", false

        @inline_editor.onSave (html, text) ->
          topic.inline_editor.disableSaveButton()
          $.post "/t/#{topic.slug}/new-post", JSON.stringify({post: html, text: text, character: topic.selected_character, avatar: $("#avatar-picker-#{topic.inline_editor.quillID}").val()}), (data) =>
            topic.inline_editor.enableSaveButton()
            if data.closed_topic?
              topic.inline_editor.flashError "Topic Closed: #{data.closed_message}"

            if data.no_content?
              topic.inline_editor.flashError "Your post has no text."

            if data.error?
              topic.inline_editor.flashError data.error

            if data.success?
              topic.inline_editor.clearEditor()
              socket.emit "event",
                room: "topic--#{topic.slug}"
                post: data.newest_post
                count: data.count

              if topic.page == topic.max_pages
                data.newest_post.author_online = true
                data.newest_post.show_boop = true
                data.newest_post.can_boop = false
                data.newest_post._is_topic_mod = topic.is_mod
                data.newest_post._is_logged_in = topic.is_logged_in
                data.newest_post.author_login_name = window.woe_is_me
                data.newest_post._show_character_badge = not window.roleplay_area
                $("#post-container").append topic.postHTML data.newest_post
                window.addExtraHTML $("#post-"+data.newest_post._id)
              else
                window.location = "/t/#{topic.slug}/page/1/post/latest_post"

      $("#post-container").delegate ".go-to-end-of-page", "click", (e) ->
        e.preventDefault()
        $("#new-post-box")[0].scrollIntoView()

      $("#post-container").delegate ".boop-button", "click", (e) ->
        e.preventDefault()
        element = $(this)
        current_status = element.data("status")
        count = parseInt(element.data("count"))
        pk = element.data("pk")

        $.post "/boop-post", JSON.stringify({pk: pk}), (data) ->
          if current_status == "notbooped"
            element.children(".boop-text").html("""<img src="/static/emoticons/brohoof_by_angelishi-d6wk2et.gif">""")
            element.children(".badge").text("")
            element.data("status", "booped")
            element.data("count", count+1)
            # element.children(".boop-text").text(" Unboop.")
            # element.children(".badge").text(count+1)
            # element.children(".badge").css("background-color", "green")
          else
            element.children(".boop-text").html("")
            element.data("status", "notbooped")
            element.children(".boop-text").text(" Boop!")
            element.data("count", count-1)
            element.children(".badge").text(element.data("count"))
            element.children(".badge").css("background-color", "#555")

      getSelectionParentElement = () ->
        parentEl = null
        sel = null
        if window.getSelection
          sel = window.getSelection()
          if sel.rangeCount
            parentEl = sel.getRangeAt(0).commonAncestorContainer
            if parentEl.nodeType != 1
              parentEl = parentEl.parentNode;
        else if sel == document.selection and sel.type != "Control"
          parentEl = sel.createRange().parentElement()
        return parentEl;

      getSelectionText = () ->
        text = ""
        if window.getSelection
          text = window.getSelection().toString();
        else if document.selection and document.selection.type != "Control"
          text = document.selection.createRange().text;
        return text

      $("#post-container").delegate ".reply-button", "click", (e) ->
        e.preventDefault()

        try
          post_object = getSelectionParentElement().closest(".post-content")
        catch
          post_object = null
        highlighted_text = getSelectionText().trim()

        element = $(this)
        my_content = ""
        $.get "/t/#{topic.slug}/edit-post/#{element.data("pk")}", (data) ->
          if post_object? and post_object == $("#post-#{element.data("pk")}")[0]
            my_content = "[reply=#{element.data("pk")}:post:#{data.author}]\n#{highlighted_text}\n[/reply]"
          else
            my_content = "[reply=#{element.data("pk")}:post:#{data.author}]\n\n"

          x = window.scrollX
          y = window.scrollY
          try
            topic.inline_editor.quill.focus()
          catch
            current_position = 0

          window.scrollTo x, y
          unless current_position?
            current_position = topic.inline_editor.quill.getSelection()?.start
            unless current_position?
              current_position = topic.inline_editor.quill.getLength()
          topic.inline_editor.quill.insertText current_position, my_content

      $("#post-container").delegate ".toggle-show-roles-button", "click", (e) ->
        $(this).parent().children(".roles-div").toggle()

      $("#post-container").delegate ".mention-button", "click", (e) ->
        e.preventDefault()
        element = $(this)
        x = window.scrollX
        y = window.scrollY
        try
          topic.inline_editor.quill.focus()
        catch
          current_position = 0

        window.scrollTo x, y
        unless current_position?
          current_position = topic.inline_editor.quill.getSelection()?.start
          unless current_position?
            current_position = topic.inline_editor.quill.getLength()

        topic.inline_editor.quill.insertText current_position, "[@#{element.data("author")}], "

      $("#post-container").delegate ".post-edit", "click", (e) ->
        e.preventDefault()
        element = $(this)
        post_content = $("#post-"+element.data("pk"))
        post_buttons = $("#post-buttons-"+element.data("pk"))
        post_character = element.data("character")
        if element.data("author")?
          post_author = element.data("author")
        else
          post_author = window.woe_is_me
        post_buttons.hide()

        inline_editor = new InlineEditor "#post-"+element.data("pk"), "/t/#{topic.slug}/edit-post/#{element.data("pk")}", true, true
        inline_editor.onReady () ->
          if topic.characters.length > 0 and window.woe_is_me == post_author
            quill_id = inline_editor.quillID
            # $("#upload-files-#{quill_id}").after """
            #   <button type="button" class="btn btn-default post-post" style="margin-left: 3px;" id="character-picker-#{quill_id}">Characters</button>
            #   """
            characterPickerTemplate = """
            <!-- <label style="margin-left: 10px;">Character Picker: </label> -->
            <select id="character-picker-{{quill_id}}" style="margin-left: 5px; width: 300px;">
              <option value="" selected></option>
              {{#each characters}}
              <option value="{{slug}}" data-image="{{default_avvie}}" {{#if default}}selected{{/if}}>
                  {{name}}
              </option>
              {{/each}}
            </select>
            """
            characterPickerHTML = Handlebars.compile(characterPickerTemplate)
            avatarPickerTemplate = """
            <!-- <label style="margin-left: 10px;">Character Picker: </label> -->
            <select id="avatar-picker-{{quill_id}}" style="margin-left: 5px; width: 80px;">
              <option value="" selected></option>
              {{#each avatars}}
              <option value="{{id}}" data-count="{{@index}}" data-image="{{url}}" {{#if @first}}selected{{/if}}>
              </option>
              {{/each}}
            </select>
            """
            avatarPickerHTML = Handlebars.compile(avatarPickerTemplate)
            for character in topic.characters
              if character.slug == post_character
                character.default = true
            $("#inline-editor-buttons-#{quill_id}").append(characterPickerHTML({characters: topic.characters, quill_id: quill_id}))
            $("#character-picker-#{quill_id}").select2
              templateResult: (result) ->
                __element = $(result.element)
                image = __element.data("image")
                if image?
                  return """
                  <div class="media-left">
                    <img src="#{image}" style="max-width: 50px;" />
                  </div>
                  <div class="media-body">
                    #{__element.text()}
                  </div>
                  """
                else
                  return "Clear Character"
              escapeMarkup: (text) ->
                return text

            $("#character-picker-#{quill_id}").on "select2:select", (e) =>
              topic["selected_character_#{quill_id}"] = $("#character-picker-#{quill_id}").val()
              if $("#avatar-picker-#{quill_id}").length > 0
                try
                  $("#avatar-picker-#{quill_id}").select2("destroy")
                  $("#avatar-picker-#{quill_id}").remove()
                catch

              selected = {}
              for character in topic.characters
                if character.slug == $("#character-picker-#{quill_id}").val()
                  selected = character
                  break
              if selected.alternate_avvies.length > 0
                $("#inline-editor-buttons-#{quill_id}").append(avatarPickerHTML({avatars: selected.alternate_avvies, quill_id: quill_id}))
                $("#avatar-picker-#{quill_id}").select2
                  templateResult: (result) ->
                    __element = $(result.element)
                    image = __element.data("image")
                    if image?
                      return """
                      <img src="#{image}" style="max-width: 50px;" />
                      """
                  templateSelection: (result) ->
                    __element = $(result.element)
                    alt = __element.data("count")+1
                    return """
                      #{alt}
                      """
                  escapeMarkup: (text) ->
                    return text

                $("#avatar-picker-#{quill_id}").on "select2:select", (e) =>
                  topic["selected_avatar_#{quill_id}"] = $("#avatar-picker-#{quill_id}").val()

        inline_editor.onSave (html, text, edit_reason) ->
          quill_id = inline_editor.quillID
          character = $("#character-picker-#{quill_id}").val()
          avatar = $("#avatar-picker-#{quill_id}").val()

          $.post "/t/#{topic.slug}/edit-post", JSON.stringify({pk: element.data("pk"), post: html, text: text, edit_reason: edit_reason, character: character, avatar: avatar}), (data) =>
            if data.error?
              inline_editor.flashError data.error

            if data.success?
              inline_editor.destroyEditor()
              post_content.html data.html
              window.addExtraHTML post_content
              post_buttons.show()

        inline_editor.onCancel (html, text) ->
          inline_editor.destroyEditor()
          inline_editor.resetElementHtml()
          window.addExtraHTML $("#post-"+element.data("pk"))
          post_buttons.show()

      $("nav.pagination-listing").delegate "#previous-page", "click", (e) ->
        e.preventDefault()
        element = $(this)
        if topic.page != 1
          $(".change-page").parent().removeClass("active")
          topic.page--
          do topic.refreshPosts

      $("nav.pagination-listing").delegate "#next-page", "click", (e) ->
        e.preventDefault()
        element = $(this)
        if topic.page != topic.max_pages
          $(".change-page").parent().removeClass("active")
          topic.page++
          do topic.refreshPosts

      $("nav.pagination-listing").delegate ".change-page", "click", (e) ->
        e.preventDefault()
        element = $(this)
        topic.page = parseInt(element.text())
        do topic.refreshPosts

      $("nav.pagination-listing").delegate "#go-to-end", "click", (e) ->
        e.preventDefault()
        element = $(this)
        topic.page = parseInt(topic.max_pages)
        do topic.refreshPosts

      $("nav.pagination-listing").delegate "#go-to-start", "click", (e) ->
        e.preventDefault()
        element = $(this)
        topic.page = 1
        do topic.refreshPosts

      popped = ('state' in window.history)
      initialURL = location.href
      $(window).on "popstate", (e) ->
        initialPop = !popped && location.href == initialURL
        popped = true
        if initialPop
          return

        setTimeout(() ->
          window.location = window.location
        , 200)

      window.RegisterAttachmentContainer "#post-container"

      $.post "/user-characters-api", {}, (data) =>
        @characters = data.characters
        if @characters.length > 0
          try
            quill_id = @inline_editor.quillID
          catch
            return false
          # $("#upload-files-#{quill_id}").after """
          #   <button type="button" class="btn btn-default post-post" style="margin-left: 3px;" id="character-picker-#{quill_id}">Characters</button>
          #   """
          characterPickerTemplate = """
          <!-- <label style="margin-left: 10px;">Character Picker: </label> -->
          <select id="character-picker-{{quill_id}}" style="margin-left: 5px; width: 300px;">
            <option value="" selected></option>
            {{#each characters}}
            <option value="{{slug}}" data-image="{{default_avvie}}">
                {{name}}
            </option>
            {{/each}}
          </select>
          """
          characterPickerHTML = Handlebars.compile(characterPickerTemplate)
          avatarPickerTemplate = """
          <!-- <label style="margin-left: 10px;">Character Picker: </label> -->
          <select id="avatar-picker-{{quill_id}}" style="margin-left: 5px; width: 80px;">
            <option value="" selected></option>
            {{#each avatars}}
            <option value="{{id}}" data-count="{{@index}}" data-image="{{url}}" {{#if @first}}selected{{/if}}>
            </option>
            {{/each}}
          </select>
          """
          avatarPickerHTML = Handlebars.compile(avatarPickerTemplate)
          $("#upload-files-#{quill_id}").after(characterPickerHTML({characters: @characters, quill_id: quill_id}))
          $("#character-picker-#{quill_id}").select2
            templateResult: (result) ->
              element = $(result.element)
              image = element.data("image")
              if image?
                return """
                <div class="media-left">
                  <img src="#{image}" style="max-width: 50px;" />
                </div>
                <div class="media-body">
                  #{element.text()}
                </div>
                """
              else
                return "Clear Character"
            escapeMarkup: (text) ->
              return text

          $("#character-picker-#{quill_id}").on "select2:select", (e) =>
            @selected_character = $("#character-picker-#{quill_id}").val()
            if $("#avatar-picker-#{quill_id}").length > 0
              try
                $("#avatar-picker-#{quill_id}").select2("destroy")
                $("#avatar-picker-#{quill_id}").remove()
              catch

            selected = {}
            for character in @characters
              if character.slug == $("#character-picker-#{quill_id}").val()
                selected = character
                break
            if selected.alternate_avvies.length > 0
              $("#inline-editor-buttons-#{quill_id}").append(avatarPickerHTML({avatars: selected.alternate_avvies, quill_id: quill_id}))
              $("#avatar-picker-#{quill_id}").select2
                templateResult: (result) ->
                  element = $(result.element)
                  image = element.data("image")
                  if image?
                    return """
                    <img src="#{image}" style="max-width: 50px;" />
                    """
                templateSelection: (result) ->
                  element = $(result.element)
                  alt = element.data("count")+1
                  return """
                    #{alt}
                    """
                escapeMarkup: (text) ->
                  return text

              # $("#avatar-picker-#{quill_id}").on "select2:select", (e) =>
              #   @selected_avatar = $("#avatar-picker-#{quill_id}").val()

    paginationHTMLTemplate: () ->
      return """
          <ul class="pagination">
            <li>
              <a href="" aria-label="Start" id="go-to-start">
                <span aria-hidden="true">Go to Start</span>
              </a>
            </li>
            <li>
              <a href="" aria-label="Previous" id="previous-page">
                <span aria-hidden="true">&laquo;</span>
              </a>
            </li>
            {{#each pages}}
            <li><a href="" class="change-page page-link-{{this}}">{{this}}</a></li>
            {{/each}}
            <li>
              <a href="" aria-label="Next" id="next-page">
                <span aria-hidden="true">&raquo;</span>
              </a>
            </li>
            <li>
              <a href="" aria-label="End" id="go-to-end">
                <span aria-hidden="true">Go to End</span>
              </a>
            </li>
          </ul>
      """

    postHTMLTemplate: () ->
      return """
            <li class="list-group-item post-listing-info">
              <div class="row">
                <div class="col-xs-4 hidden-md hidden-lg">
                  {{#unless character_avatar}}
                    <a href="/member/{{author_login_name}}"><img src="{{user_avatar_60}}" width="{{user_avatar_x_60}}" height="{{user_avatar_y_60}}" class="avatar-mini"></a>
                  {{else}}
                    <a href={{#unless _show_character_badge}}"/characters/{{character_slug}}" target="_blank"{{else}}"/member/{{author_login_name}}"{{/unless}}><img src="{{character_avatar_small}}" style="max-width: 60px;" class="avatar-mini"></a>
                  {{/unless}}
                </div>
                <div class="col-md-3 col-xs-8">
                  {{#if author_online}}
                  <b><span class="glyphicon glyphicon-ok-sign" aria-hidden="true"></span> <a class="hover_user" href="/member/{{author_login_name}}">{{#unless character_name}}{{author_name}}{{else}}{{character_name}}{{/unless}}</a></b>
                  {{else}}
                  <b><span class="glyphicon glyphicon-minus-sign" aria-hidden="true"></span> <a class="hover_user" href="/member/{{author_login_name}}" class="inherit_colors">{{#unless character_name}}{{author_name}}{{else}}{{character_name}}{{/unless}}</a></b>
                  {{/if}}
                  <span class="hidden-md hidden-sm hidden-lg">
                  {{#unless roles}}
                  {{#unless character_name}}
                    <span style="color:#F88379;"><strong>Members</strong></span><br>
                  {{else}}
                    <span style="color:#B00E0E;"><strong>Characters</strong></span><br>
                  {{/unless}}
                  {{else}}
                  {{#if roles}}
                  {{#each roles}}
                  {{#if @first}}
                  <strong>{{{this}}}</strong>
                  {{/if}}
                  {{/each}}
                  {{/if}}
                  {{/unless}}
                  </span>
                  {{#unless character_name}}
                    <span style="color:#F88379;" class="hidden-xs"><strong>Members</strong></span><br>
                  {{else}}
                    <span style="color:#B00E0E;" class="hidden-xs"><strong>Characters</strong></span><br>
                  {{/unless}}
                  <span class="hidden-md hidden-lg">Posted {{created}}</span>
                </div>
                <div class="col-md-9 hidden-xs hidden-sm">
                  <span id="post-number-1" class="post-number" style="vertical-align: top;"><a href="{{direct_url}}" id="postlink-{{_id}}">\#{{_id}}</a></span>
                  Posted {{created}}
                </div>
              </div>
            </li>
            <li class="list-group-item post-listing-post">
              <div class="row">
                <div class="col-md-3" style="text-align: center;">
                  {{#unless character_avatar}}
                    <a href="/member/{{author_login_name}}"><img src="{{user_avatar}}" width="{{user_avatar_x}}" height="{{user_avatar_y}}" class="post-member-avatar hidden-xs hidden-sm"></a>
                  {{else}}
                    <a href={{#unless _show_character_badge}}"/characters/{{character_slug}}" target="_blank"{{else}}"/member/{{author_login_name}}"{{/unless}}><img src="{{character_avatar_large}}" style="max-width: 200px;" class="post-member-avatar hidden-xs hidden-sm"></a>
                  {{/unless}}
                  <span class="hidden-xs hidden-sm"><br><br>
                    {{#if character_motto}}
                    <div class="post-member-self-title">{{character_motto}}</div>
                    {{else}}
                    <div class="post-member-self-title">{{user_title}}</div>
                    {{/if}}
                    {{#if _show_character_badge}}
                    {{#if character_name}}
                    <a href="/characters/{{character_slug}}" target="_blank"><img src="/static/emoticons/button_character_by_angelishi-d6wlo5k.gif"></a>
                    {{#if roles}}
                    <br>
                    {{/if}}
                    {{/if}}
                    {{/if}}
                    {{#if roles}}
                    <a class="btn btn-default toggle-show-roles-button btn-xs" style="margin-top: 5px;">Community Roles</a>
                    <div class="roles-div" style="display: none;">
                    {{#each roles}}
                    <b>{{{this}}}</b><br>
                    {{/each}}
                    </div>
                    {{/if}}
                    <hr></span>
                  <div class="post-meta">
                  </div>
                </div>
                <div class="col-md-9 post-right">
                  <div class="post-content" id="post-{{_id}}">
                    {{{html}}}
                  </div>
                  <br>
                  <div class="row post-edit-likes-info" id="post-buttons-{{_id}}">
                      <div class="col-xs-8">
                        {{#if _is_logged_in}}
                        <div class="btn-group" role="group" aria-label="...">
                          <div class="btn-group">
                            <button type="button" class="btn btn-default mention-button" data-author="{{author_login_name}}">@</button>
                            <button type="button" class="btn btn-default reply-button" data-pk="{{_id}}">Reply</button>
                            <button type="button" class="btn btn-default report-button" data-pk="{{_id}}" data-type="post"><span class="glyphicon glyphicon-exclamation-sign"></span></button>
                            {{#if is_admin}}<a href="/admin/post/edit/?id={{_id}}" target="_blank"><button type="button" class="btn btn-default" data-type="post"><span class="glyphicon glyphicon-cog"></span></button></a>{{/if}}
                            <!-- <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                              <span class="caret"></span>
                              <span class="sr-only">Toggle Dropdown</span>
                            </button>
                            <ul class="dropdown-menu" role="menu">
                              <li><a href="">Quote</a></li>
                              <li><a href="">Multiquote</a></li>
                            </ul> -->
                          </div>
                        {{/if}}
                          {{#if _is_logged_in}}
                          <div class="btn-group" style="">
                            {{#if _is_topic_mod}}
                            <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                              <span class="caret"></span>
                              <span class="sr-only">Toggle Dropdown</span>
                            </button>
                            <ul class="dropdown-menu" role="menu">
                              <li><a href="" class="post-edit" data-pk="{{_id}}" {{#if character_name}}data-character="{{character_slug}}" data-author="{{author_login_name}}"{{/if}}>Edit Post</a></li>
                              {{#if topic_leader}}
                               <li><a href="{{topic_leader}}">Edit Topic</a></li>
                               {{#if is_admin}}
                                <li>
                                  <a href="/admin/topic/edit/?id={{_tid}}" target="_blank">Topic Admin</a>
                                </li>
                              {{/if}}
                              {{/if}}
                              <li><a href="">Hide</a></li>
                              <li class="divider hidden-md hidden-sm hidden-lg"></li>
                              <li class="hidden-md hidden-sm hidden-lg"><a class="go-to-end-of-page" href="">Go to End</a></li>
                            </ul>
                            {{else}}
                              {{#if is_author}}
                                <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                                  <span class="caret"></span>
                                  <span class="sr-only">Toggle Dropdown</span>
                                </button>
                                <ul class="dropdown-menu" role="menu">
                                  <li><a href="" class="post-edit" data-pk="{{_id}}" {{#if character_name}}data-character="{{character_slug}}" data-author="{{author_login_name}}"{{/if}}>Edit Post</a></li>
                                  {{#if topic_leader}}
                                   <li><a href="{{topic_leader}}">Edit Topic</a></li>
                                  {{/if}}
                                  <li class="divider hidden-md hidden-sm hidden-lg"></li>
                                  <li class="hidden-md hidden-sm hidden-lg"><a class="go-to-end-of-page" href="">Go to End</a></li>
                                </ul>
                              {{/if}}
                            {{/if}}
                          {{/if}}
                          </div>
                        </div>
                    </div>
                    <div class="col-xs-4 post-likes">
                      {{#if show_boop}}
                      {{#if can_boop}}
                      {{#if has_booped}}
                      <button type="button" class="btn btn-default boop-button" data-pk="{{_id}}" data-status="booped" data-count="{{boop_count}}"><span class="badge" style="background-color: green;">{{boop_count}}</span><span class="boop-text"> Unboop.</span></button>
                      {{else}}
                      <button type="button" class="btn btn-default boop-button" data-pk="{{_id}}" data-status="notbooped" data-count="{{boop_count}}"><span class="badge" style="background-color: #555;">{{boop_count}}</span><span class="boop-text">  Boop!</span></button>
                      {{/if}}
                      {{else}}
                      <span><span class="badge">{{boop_count}}</span> boops!</span>
                      {{/if}}
                      {{/if}}
                    </div>
                  </div>
                  <hr>
                  <div class="post-signature">
                    {{#if signature}}
                    {{#if is_admin}}
                    <a href="/admin/signature/edit/?id={{signature_id}}" target="_blank" class="float-right"><span class="glyphicon glyphicon-cog"></span></a>
                    {{/if}}
                    {{/if}}
                    {{#if signature}}
                    {{{signature}}}
                    {{/if}}
                  </div>
                </div>
      """

    refreshPosts: () ->
      new_post_html = ""
      $.post "/t/#{@slug}/posts", JSON.stringify({page: @page, pagination: @pagination}), (data) =>
        if not @first_load
          history.pushState({id: "topic-page-#{@page}"}, '', "/t/#{@slug}/page/#{@page}")
        else
          @first_load = false
        first_post = ((@page-1)*@pagination)+1
        for post, i in data.posts
          post.count = first_post+i
          post._is_topic_mod = @is_mod
          post._is_logged_in = @is_logged_in
          post._show_character_badge = not window.roleplay_area
          if @is_logged_in
            post.show_boop = true
          post.direct_url = "/t/#{@slug}/page/#{@page}/post/#{post._id}"
          new_post_html = new_post_html + @postHTML post

        pages = []
        @max_pages = Math.ceil data.count/@pagination
        if @max_pages > 5
          if @page > 3 and @page < @max_pages-5
            pages = [@page-2..@page+5]
          else if @page > 3
            pages = [@page-2..@max_pages]
          else if @page <= 3
            pages = [1..@page+5]
        else
          pages = [1..Math.ceil data.count/@pagination]
        pagination_html = @paginationHTML {pages: pages}

        $(".pagination-listing").html pagination_html
        $("#post-container").html new_post_html
        $(".page-link-#{@page}").parent().addClass("active")

        if window._initial_post != ""
          setTimeout () ->
            $("#postlink-#{window._initial_post}")[0].scrollIntoView()
            window._initial_post = ""
          , 300
        else
          setTimeout () ->
            $("#topic-breadcrumb")[0].scrollIntoView()
          , 300
        window.setupContent()

  window.topic = new Topic($("#post-container").data("slug"))
