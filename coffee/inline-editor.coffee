$ ->
  class InlineEditor
    constructor: (element, url = "", cancel_button=false, edit_reason=false, height=300, no_image_link=false, inline_editor=false) ->
      Dropzone.autoDiscover = false
      @quillID = do @getQuillID
      @element = $(element)
      @edit_reason = edit_reason
      @height = "#{height}px"
      @no_image_link = no_image_link
      
      if url != ""
        $.get url, (data) =>
          @element.data("editor_initial_html", data.content)
          @setupEditor cancel_button, inline_editor
      else
        @element.data("editor_initial_html", @element.html())
        @setupEditor cancel_button, inline_editor
    
    getQuillID: () ->
      return $(".ql-editor").length + 1
      
    onSave: (saveFunction) ->
      @saveFunction = saveFunction

    onReady: (readyFunction) ->
      @readyFunction = readyFunction

    onCancel: (cancelFunction) ->
      @cancelFunction = cancelFunction

    onFullPage: (fullPageFunction) ->
      @fullPageFunction = fullPageFunction

    noSaveButton: () ->
      do $("#save-text-#{@quillID}").remove

    flashError: (message) ->
      @element.parent().children(".alert").remove()
      @element.parent().prepend """<div class="alert alert-danger alert-dismissible fade in" role="alert">
          <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">×</span></button>
          #{message}
        </div>"""

    clearEditor: () ->
      @element.data("editor").setText("")
      Dropzone.forElement("#dropzone-#{@quillID}").removeAllFiles()
        
    setupEditor: (cancel_button, inline_editor) ->
      @lockSave = false
      if @edit_reason
        @element.before @editReasonHTML
      @element.before """<div id="draft-modal-#{@quillID}" class="modal fade"></div>"""
      @element.before """<div id="mention-modal-#{@quillID}" class="modal fade"></div>"""
      @element.before """<div id="emoticon-modal-#{@quillID}" class="modal fade"></div>"""
      @element.before """<div id="image-link-modal-#{@quillID}" class="modal fade"></div>"""
      @element.html(@editordivHTML())
      @element.after @previewHTML
      @element.after @dropzoneHTML
      @element.after @submitButtonHTML cancel_button
      
      @last_saved_draft = new Date().getTime() / 1000
      
      $.post "/drafts/count", JSON.stringify({quill_id: @quillID, path: window.location.pathname}), (response) =>
        if response.count > 0
          $("#draft-view-#{@quillID}").addClass("btn-success")
      
      if not inline_editor
        toolbarOptions = [
          ['bold', 'italic', 'underline', 'strike'],
          [{ 'list': 'bullet' }, { 'indent': '-1'}, { 'indent': '+1' }],
          [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
          [{ 'font': ["regular", "caption", "caviar", "comic", "monotype", "monterrey", "opensans", "zinniaseed"] }],
          [{ 'color': [] },],
          [{ 'align': [] }],
          ['link'],
          ['image'],
        ]
      else
        toolbarOptions = [
          ['bold', 'italic', 'underline', 'strike'],
        ]
      
      Font = Quill.import('formats/font')
      Font.whitelist = ['regular', 'caption', 'caviar', 'comic', 'monotype', 'monterrey', 'opensans', 'zinniaseed']
      Quill.register(Font, true);
      
      Parchment = Quill.import('parchment')
      Block = Parchment.query('block')
      Block.tagName = 'DIV'
      Quill.register(Block, true)
      
      quill = new Quill "#post-editor-#{@quillID}",
        theme: 'snow'
        modules:
          toolbar: toolbarOptions
      
      quill.on 'text-change', (delta, source) =>
        if ((new Date().getTime() / 1000) - @last_saved_draft) > (2*60)
          @last_saved_draft = new Date().getTime() / 1000
          if not @lockSave and quill.getText != ""
            $.post "/drafts/save", JSON.stringify({quill_id: @quillID, path: window.location.pathname, contents: $("#post-editor-#{@quillID}").children(".ql-editor").html()}), (response) =>
              $("#draft-view-#{@quillID}").addClass("btn-success")
      
      quill.clipboard.dangerouslyPasteHTML @element.data("editor_initial_html")
      @quill = quill
      toolbar = quill.getModule 'toolbar'

      _this = this
      @element.data("_editor", this)
      @element.data("editor", quill)
      
      toolbar.addHandler 'image', () ->
        current_position = _this.quill.getSelection(true).index
        $("#image-link-modal-#{_this.quillID}").html(
          """
            <div class="modal-dialog">
              <div class="modal-content">
                <div class="modal-header">
                  <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                  <h4 class="modal-title">Paste image URL</h4>
                </div>
                <div class="modal-body">
                  <span id="image-link-instructions">Use this to insert images into your post.</span>
                  <br><br>
                  <input id="image-link-select" class="form-control" style="max-width: 100%; width: 400px;" multiple="multiple">
                  <img id="image-link-load" src="/static/loading.gif" style="display: none;">
                </div>
                <div class="modal-footer">
                  <button type="button" class="btn btn-primary" id="image-link-modal-insert">Insert</button>
                  <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                </div>
              </div>
            </div>
          """)

        $("#image-link-modal-insert").click (e) ->
          e.preventDefault()
          _this.quill.insertEmbed current_position, 'image', $("#image-link-select").val()
          $("#image-link-modal-#{_this.quillID}").modal("hide")

        $("#image-link-modal-#{_this.quillID}").modal("show")
      
      if not inline_editor
        @element.children(".ql-toolbar").append @extraButtonsHTML
    
      $("#add-mention-#{@quillID}").on 'click', (e) =>
        do @createAndShowMentionModal
        
      $("#add-emote-#{@quillID}").on 'click', (e) =>
        do @createAndShowEmoticonModal
        
      $("#add-spoiler-#{@quillID}").on 'click', (e) =>
        quill.insertText quill.getSelection(true).index, "[spoiler=Spoiler!]\n"
        quill.insertText quill.getSelection(true).index+quill.getSelection(true).length, "[/spoiler]\n"
        
      $("#add-quote-#{@quillID}").on 'click', (e) =>
        quill.insertText quill.getSelection(true).index, "[quote=Someone]\n"
        quill.insertText quill.getSelection(true).index+quill.getSelection(true).length, "[/quote]\n"
                
      $("#add-roll-#{@quillID}").on 'click', (e) =>
        quill.insertText quill.getSelection(true).index, "[roll=1d6]Rolling a thing![/roll]"
                
      $("#add-progress-#{@quillID}").on 'click', (e) =>
        quill.insertText quill.getSelection(true).index, "[progressbar=pink]50[/progressbar]"
                
      $("#toolbar-#{@quillID}").find(".ql-image-link").click (e) =>
        do @createAndShowImageLinkModal
        
      $("#dropzone-#{@quillID}").dropzone
        url: "/attach"
        dictDefaultMessage: "Click here or drop a file in to upload (image files only)."
        acceptedFiles: "image/jpeg,image/jpg,image/png,image/gif"
        maxFilesize: 30
        init: () ->
          this.on "success", (file, response) ->
            quill.insertText quill.getSelection(true).index, "[attachment=#{response.attachment}:#{response.xsize}]"
            
      $("#upload-files-#{@quillID}").click (e) =>
        e.preventDefault()
        if $("#dropzone-#{@quillID}").is(":visible")
          $("#dropzone-#{@quillID}").hide()
        else
          $("#dropzone-#{@quillID}").show()
          
      $("#draft-view-#{@quillID}").click (e) =>
        $.post "/drafts/list", JSON.stringify({quill_id: @quillID, path: window.location.pathname}), (response) =>
          @createAndShowDraftModal response.drafts

      $("#save-text-#{@quillID}").click (e) =>
        e.preventDefault()
        @lockSave = true
        if @saveFunction?
          $.post "/drafts/clear", JSON.stringify({quill_id: @quillID, path: window.location.pathname}), (response) =>
            if @edit_reason
              @saveFunction $("#post-editor-#{@quillID}").children(".ql-editor").html(), @element.data("editor").getText(), $("#edit-reason-#{@quillID}").val()
            else
              @saveFunction $("#post-editor-#{@quillID}").children(".ql-editor").html(), @element.data("editor").getText()
            $("#draft-view-#{@quillID}").removeClass("btn-success")
            @lockSave = false

      $("#cancel-edit-#{@quillID}").click (e) =>
        e.preventDefault()
        if @cancelFunction?
          @cancelFunction $("#post-editor-#{@quillID}").children(".ql-editor").html(), @element.data("editor").getText()

      $("#preview-#{@quillID}").click (e) =>
        e.preventDefault()
        $("#preview-box-#{@quillID}").parent().show()

        $.post "/preview", JSON.stringify({text: $("#post-editor-#{@quillID}").children(".ql-editor").html()}), (response) =>
          $("#preview-box-#{@quillID}").html response.preview
          window.addExtraHTML("#preview-box-#{@quillID}")

      if @readyFunction?
        do @readyFunction

    getHTML: () =>
      $("#post-editor-#{@quillID}").children(".ql-editor").html()

    setElementHtml: (set_html) ->
      @element.data("given_editor_initial_html", set_html)

    resetElementHtml: () ->
      if @element.data("given_editor_initial_html")?
        @element.html(@element.data("given_editor_initial_html"))
      else
        @element.html(@element.data("editor_initial_html"))
      
    extraButtonsHTML: () =>
      """
      <span class="ql-formats">
        <button type="button" id="add-quote-#{@quillID}" class="ql-quote glyphicon glyphicon-comment">&nbsp;</button>
        <button type="button" id="add-progress-#{@quillID}" class="ql-progress glyphicon glyphicon-signal">&nbsp;</button>
        <button type="button" id="add-mention-#{@quillID}" class="ql-mention" >@</button>
        <button type="button" id="add-emote-#{@quillID}" class="ql-emote" >&#9786;</button>
        <button type="button" id="add-spoiler-#{@quillID}" class="ql-spoiler">S</button>
        <button type="button" id="add-roll-#{@quillID}" class="ql-roll">D6</button>
      </span>
      """
      
    editReasonHTML: () =>
      return """
        <div class="form-inline">
          <div class="form-group">
            <label>Edit Reason: </label>
            <input class="form-control" id="edit-reason-#{@quillID}" type="text" initial=""></input>
          </div>
        </form>
        <br><br>
      """
      
    disableSaveButton: () =>
      $("#save-text-#{@quillID}").addClass("disabled")
      $("#upload-files-#{@quillID}").addClass("disabled")
      $("#cancel-edit-#{@quillID}").addClass("disabled")

    enableSaveButton: () =>
      $("#save-text-#{@quillID}").removeClass("disabled")
      $("#upload-files-#{@quillID}").removeClass("disabled")
      $("#cancel-edit-#{@quillID}").removeClass("disabled")

    dropzoneHTML: () =>
      return """
          <div id="dropzone-#{@quillID}" class="dropzone" style="display: none;"></div>
      """

    previewHTML: () =>
      return """
          <div class="panel panel-default" id="preview-container-#{@quillID}" style="display: none;">
            <div class="panel-heading">Post Preview (Click Preview Button to Update)</div>
            <div id="preview-box-#{@quillID}" class="panel-body"></div>
          </div>
      """

    editordivHTML: () =>
      return """
        <div id="post-editor-#{@quillID}" class="editor-box" style="height: #{@height};" data-placeholder=""></div>
      """
      
    submitButtonHTML: (cancel_button=false) =>
      if cancel_button == true
        return """
          <div id="inline-editor-buttons-#{@quillID}" class="inline-editor-buttons">
            <button type="button" class="btn btn-default post-post" id="save-text-#{@quillID}">Post</button>
            <button type="button" class="btn btn-default post-post" id="draft-view-#{@quillID}">Drafts</button>
            <button type="button" class="btn btn-default post-post" id="upload-files-#{@quillID}">Upload Files</button>
            <button type="button" class="btn btn-default" id="cancel-edit-#{@quillID}">Close</button>
            <button type="button" class="btn btn-default" id="preview-#{@quillID}">Preview</button>
          </div>
        """
      else
        return """
          <div id="inline-editor-buttons-#{@quillID}" class="inline-editor-buttons">
            <button type="button" class="btn btn-default post-post" id="save-text-#{@quillID}">Post</button>
            <button type="button" class="btn btn-default post-post" id="draft-view-#{@quillID}">Drafts</button>
            <button type="button" class="btn btn-default post-post" id="upload-files-#{@quillID}">Upload Files</button>
            <button type="button" class="btn btn-default" id="preview-#{@quillID}">Preview</button>
          </div>
        """
        
    destroyEditor: () ->
      @element.data("editor_is_active", false)
      @element.parent().children(".alert").remove()
      do $("#inline-editor-buttons-#{@quillID}").remove
      do $("#toolbar-#{@quillID}").remove
      do $("#post-editor-#{@quillID}").remove
      Dropzone.forElement("#dropzone-#{@quillID}").destroy()
      do $("#dropzone-#{@quillID}").remove
      do $("#emoticon-modal-#{@quillID}").remove
      do $("#mention-modal-#{@quillID}").remove
      do $("#preview-container-#{@quillID}").remove
      do $("#edit-reason-#{@quillID}").parent().parent().remove

    createAndShowEmoticonModal: () =>
      current_position = this.quill.getSelection(true).index
      $("#emoticon-modal-#{@quillID}").html(
        """
          <div class="modal-dialog">
            <div class="modal-content">
              <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
              </div>
              <div class="modal-body">
                <img src="/static/emotes/angry.png" class="emoticon-listing" data-emotecode=" :anger: ">
                <img src="/static/emotes/smile.png" class="emoticon-listing" data-emotecode=" :) ">
                <img src="/static/emotes/sad.png" class="emoticon-listing" data-emotecode=" :( ">
                <img src="/static/emotes/heart.png" class="emoticon-listing" data-emotecode=" :heart: ">
                <img src="/static/emotes/oh.png" class="emoticon-listing" data-emotecode=" :surprise: ">
                <img src="/static/emotes/wink.png" class="emoticon-listing" data-emotecode=" :wink: ">
                <img src="/static/emotes/cry.png" class="emoticon-listing" data-emotecode=" :cry: ">
                <img src="/static/emotes/tongue.png" class="emoticon-listing" data-emotecode=" :silly: ">
                <img src="/static/emotes/embarassed.png" class="emoticon-listing" data-emotecode=" :blushing: ">
                <img src="/static/emotes/biggrin.png" class="emoticon-listing" data-emotecode=" :lol: ">
            </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
              </div>
            </div>
          </div>
        """)

      _this = this
      $(".emoticon-listing").click (e) ->
        e.preventDefault()
        emoticon_code = $(this).data("emotecode")
        _this.quill.insertText current_position, emoticon_code
        $("#emoticon-modal-#{_this.quillID}").modal("hide")

      $("#emoticon-modal-#{@quillID}").modal("show")
    
    createAndShowDraftModal: (drafts) =>
      draft_picks_html = ""
      for draft in drafts
        draft_picks_html = draft_picks_html + """
            <div style="margin-top: 5px;">
            <a href="#" data-id="#{draft.id}" class="draft-select-#{@quillID} btn btn-xs btn-default">#{draft.time}</a>
            <div class="content-spoiler" style="height: 150px;overflow: scroll; border: 1px lightgray solid !important; margin: 0px 0px 10px 0px; padding: 10px; display: none;"><div>
              #{draft.contents}
            </div></div>
            </div>
        """
        
      $("#draft-modal-#{@quillID}").html(
        """
            <div class="modal-dialog">
              <div class="modal-content">
                <div class="modal-header">
                  <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                  <h4 class="modal-title">Restore Draft</h4>
                </div>
                <div class="modal-body">
                  #{draft_picks_html}
                </div>
                <div class="modal-footer">
                  <button type="button" class="btn btn-default" id="manual-save-#{@quillID}" >Manual Save</button>
                  <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                </div>
              </div>
            </div>
        """
      )
      window.addExtraHTML "#draft-modal-#{@quillID}"
      $("#draft-modal-#{@quillID}").find(".toggle-spoiler").css("margin-top", "0px")
      $("#draft-modal-#{@quillID}").find(".toggle-spoiler").text "Preview"
      
      $(".draft-select-#{@quillID}").click (e) =>
        e.preventDefault()
        _id = $(e.target).data("id")
        @lockSave = true
        $.post "/drafts/get", JSON.stringify({quill_id: @quillID, path: window.location.pathname, id: _id}), (response) =>
          @quill.clipboard.dangerouslyPasteHTML response.contents
          $("#draft-modal-#{@quillID}").modal("hide")
          @lockSave = false
      
      $("#manual-save-#{@quillID}").click (e) =>
        e.preventDefault()
        $("#draft-modal-#{@quillID}").modal("hide")
        $.post "/drafts/save", JSON.stringify({quill_id: @quillID, path: window.location.pathname, contents: $("#post-editor-#{@quillID}").children(".ql-editor").html()}), (response) =>
          $("#draft-view-#{@quillID}").addClass("btn-success")
      
      $("#draft-modal-#{@quillID}").modal("show")
    
    createAndShowMentionModal: () =>
      $("#mention-modal-#{@quillID}").html(
        """
          <div class="modal-dialog">
            <div class="modal-content">
              <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                <h4 class="modal-title">Mention Lookup</h4>
              </div>
              <div class="modal-body">
                Use this to insert mentions into your post.
                <br><br>
                <select id="member-select" class="form-control" style="max-width: 100%; width: 400px;" multiple="multiple">
                </select>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-primary" id="mention-modal-insert">Insert</button>
                <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
              </div>
            </div>
          </div>
        """)
      $("#member-select").select2
        ajax:
          url: "/user-list-api-variant",
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
        
      $("#mention-modal-insert").click (e) =>
        e.preventDefault()

        __text = ""
        for val, i in $("#member-select").val()
          __text = __text + "[@#{val}]"
          unless i == $("#member-select").val().length-1
            __text = __text + ", "

        @quill.insertText @quill.getSelection(true).index, __text

        $("#mention-modal-#{@quillID}").modal("hide")

      $("#mention-modal-#{@quillID}").modal("show")
    
    window.InlineEditor = InlineEditor
    