$ ->
  class InlineEditor
    constructor: (element, url = "", cancel_button=false, edit_reason=false, height=300, no_image_link=false) ->
      Dropzone.autoDiscover = false
      @quillID = do @getQuillID
      @element = $(element)
      @edit_reason = edit_reason
      @height = "#{height}px"
      @no_image_link = no_image_link
      
      if url != ""
        $.get url, (data) =>
          @element.data("editor_initial_html", data.content)
          @setupEditor cancel_button
      else
        @element.data("editor_initial_html", @element.html())
        @setupEditor cancel_button
    
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
        
    setupEditor: (cancel_button) ->
      if @edit_reason
        @element.before @editReasonHTML
      @element.before """<div id="mention-modal-#{@quillID}" class="modal fade"></div>"""
      @element.before """<div id="emoticon-modal-#{@quillID}" class="modal fade"></div>"""
      @element.before """<div id="image-link-modal-#{@quillID}" class="modal fade"></div>"""
      @element.html(@editordivHTML())
      @element.after @dropzoneHTML
      @element.after @previewHTML
      @element.after @submitButtonHTML cancel_button
      
      toolbarOptions = [
        ['bold', 'italic', 'underline', 'strike'],
        ['blockquote', 'code-block'],
        [{ 'header': 1 }, { 'header': 2 }],
        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
        [{ 'script': 'sub'}, { 'script': 'super' }],
        [{ 'indent': '-1'}, { 'indent': '+1' }],
        [{ 'direction': 'rtl' }],
        [{ 'size': ['small', false, 'large', 'huge'] }],
        [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
        [{ 'color': [] }, { 'background': [] }],
        [{ 'font': [] }],
        [{ 'align': [] }],
        ['clean'],
        ['link'],
        ['image'],
      ]
      
      Parchment = Quill.import('parchment')
      Block = Parchment.query('block')
      Block.tagName = 'DIV'
      Quill.register(Block, true)
       
      quill = new Quill "#post-editor-#{@quillID}",
        theme: 'snow'
        modules:
          toolbar: toolbarOptions
      
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
                  <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
                </div>
              </div>
            </div>
          """)

        $("#image-link-modal-insert").click (e) ->
          e.preventDefault()
          _this.quill.insertEmbed current_position, 'image', $("#image-link-select").val()
          $("#image-link-modal-#{_this.quillID}").modal("hide")

        $("#image-link-modal-#{_this.quillID}").modal("show")
              
      @element.children(".ql-toolbar").append @extraButtonsHTML
    
      $("#add-mention-#{@quillID}").on 'click', (e) =>
        do @createAndShowMentionModal
        
      $("#add-emote-#{@quillID}").on 'click',  (e) =>
        do @createAndShowEmoticonModal
        
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

      $("#save-text-#{@quillID}").click (e) =>
        e.preventDefault()
        if @saveFunction?
          if @edit_reason
            @saveFunction $("#post-editor-#{@quillID}").children(".ql-editor").html(), @element.data("editor").getText(), $("#edit-reason-#{@quillID}").val()
          else
            @saveFunction $("#post-editor-#{@quillID}").children(".ql-editor").html(), @element.data("editor").getText()

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
        <button type="button" id="add-mention-#{@quillID}" class="ql-mention" >@</button>
        <button type="button" id="add-emote-#{@quillID}" class="ql-mention" >&#9786;</button>
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
            <button type="button" class="btn btn-default post-post" id="save-text-#{@quillID}">Save</button>
            <button type="button" class="btn btn-default post-post" id="upload-files-#{@quillID}">Upload Files</button>
            <button type="button" class="btn btn-default" id="cancel-edit-#{@quillID}">Cancel</button>
            <button type="button" class="btn btn-default" id="preview-#{@quillID}">Preview</button>
          </div>
        """
      else
        return """
          <div id="inline-editor-buttons-#{@quillID}" class="inline-editor-buttons">
            <button type="button" class="btn btn-default post-post" id="save-text-#{@quillID}">Save</button>
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
                <h4 class="modal-title">Pick an Emote! <img src="/static/emoticons/fluttershy_happy_by_angelishi.gif"></h4>
              </div>
              <div class="modal-body">
                <img src="/static/emoticons/fluttershy_happy_by_angelishi.gif" class="emoticon-listing" data-emotecode=":)">
                <img src="/static/emoticons/fluttershy_sad_by_angelishi.gif" class="emoticon-listing" data-emotecode=":(">
                <img src="/static/emoticons/shocked_fluttershy_by_angelishi-d7xyd7j.gif" class="emoticon-listing" data-emotecode=":horror:">
                <img src="/static/emoticons/embarrassed_fluttershy_by_angelishi-d7xyd7k.gif" class="emoticon-listing" data-emotecode=":shy:">
               <img src="/static/emoticons/applejack_confused_by_angelishi-d6wk2ew.gif" class="emoticon-listing" data-emotecode=":wat:">
                <img src="/static/emoticons/nervous_aj_by_angelishi-d7ahd5y.gif" class="emoticon-listing" data-emotecode=":S">
                <img src="/static/emoticons/liar_applejack_by_angelishi-d7aglwl.gif" class="emoticon-listing" data-emotecode=":liarjack:">
                <img src="/static/emoticons/pinkie_laugh_by_angelishi-d6wk2ek.gif" class="emoticon-listing" data-emotecode=":D">
                <img src="/static/emoticons/pinkie_mustache_by_angelishi-d6wk2eh.gif" class="emoticon-listing" data-emotecode=":mustache:">
                <img src="/static/emoticons/pinkie_silly_by_angelishi-d6wk2ef.gif" class="emoticon-listing" data-emotecode=":P">
                <img src="/static/emoticons/pinkamena_by_angelishi-d6wk2er.gif" class="emoticon-listing" data-emotecode=":pinkamena:">
                <img src="/static/emoticons/rarity_happy_by_angelishi.gif" class="emoticon-listing" data-emotecode=":pleased:">
                <img src="/static/emoticons/rarity_shock_2_by_angelishi-d6wk2eb.gif" class="emoticon-listing" data-emotecode=":shocked:">
                <img src="/static/emoticons/singing_rarity_by_angelishi-d7agp33.gif" class="emoticon-listing" data-emotecode=":sing:">
                <img src="/static/emoticons/twilight___twitch_by_angelishi.gif" class="emoticon-listing" data-emotecode=":twitch:">
                <img src="/static/emoticons/twilight_think_by_angelishi.gif" class="emoticon-listing" data-emotecode=":?">
                <img src="/static/emoticons/twilight_wink_by_angelishi.gif" class="emoticon-listing" data-emotecode=";)">
                <img src="/static/emoticons/rd_yawn_by_angelishi-d9cwc1o.gif" class="emoticon-listing" data-emotecode=":yawn:">
                <img src="/static/emoticons/rainbowdash_cool_by_angelishi.gif" class="emoticon-listing" data-emotecode=":cool:">
                <img src="/static/emoticons/rd_laugh_by_angelishi-d7aharw.gif" class="emoticon-listing" data-emotecode=":rofl:">
                <img src="/static/emoticons/scootaloo_want_face_by_angelishi-d7xyd7g.gif" class="emoticon-listing" data-emotecode=":want:">
                <img src="/static/emoticons/derpy_by_angelishi-d7amv0j.gif" class="emoticon-listing" data-emotecode=":derp:">
                <img src="/static/emoticons/head_wobble_by_angelishi-d9cwc16.gif" class="emoticon-listing" data-emotecode=":jester:">
                <img src="/static/emoticons/love_spike_by_angelishi-d7amv0g.gif" class="emoticon-listing" data-emotecode=":love:">
  <br>
                <img src="/static/emoticons/celestia_noapproval_by_angelishi-d9cwc1c.png" class="emoticon-listing" data-emotecode=":unamused:">
                <img src="/static/emoticons/celestia_playful_by_angelishi-d9cwc1g.gif" class="emoticon-listing" data-emotecode=":playful:">
                <img src="/static/emoticons/luna_please_by_angelishi-d9cwc1l.gif" class="emoticon-listing" data-emotecode=":plz:">
                <img src="/static/emoticons/discord_troll_laugh_by_angelishi-d7xyd7m.gif" class="emoticon-listing" data-emotecode=":troll:">
                <img src="/static/emoticons/sun_happy_by_angelishi-d6wlo5g.gif" class="emoticon-listing" data-emotecode=":sunjoy:">
                <img src="/static/emoticons/moon_by_angelishi-d7amv0a.gif" class="emoticon-listing" data-emotecode=":moonjoy:">
          <img src="/static/emoticons/brohoof_by_angelishi-d6wk2et.gif" class="emoticon-listing" data-emotecode=":hoofbump:">              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
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
                <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
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
    