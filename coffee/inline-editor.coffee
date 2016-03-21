$ ->
  class InlineEditor
    constructor: (element, url = "", cancel_button=false, edit_reason=false, height=300) ->
      Dropzone.autoDiscover = false
      @quillID = do @getQuillID
      @element = $(element)
      if @element.data("editor_is_active")
        return false
      @element.data("editor_is_active", true)
      @edit_reason = edit_reason
      @height="#{height}px"

      if url != ""
        $.get url, (data) =>
          @element.data("editor_initial_html", data.content)
          @setupEditor cancel_button
      else
        @element.data("editor_initial_html", @element.html())
        @setupEditor cancel_button

    createAndShowImageLinkModal: () =>
      this.quill.focus()
      current_position = this.quill.getSelection()?.start
      unless current_position?
        current_position = this.quill.getLength()

      $("#image-link-modal-#{@quillID}").html(
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

      _this = this
      $("#image-link-modal-insert").click (e) ->
        e.preventDefault()
        _this.quill.insertEmbed current_position, 'image', $("#image-link-select").val()
        $("#image-link-modal-#{_this.quillID}").modal("hide")

      $("#image-link-modal-#{@quillID}").modal("show")

    createAndShowEmoticonModal: () =>
      this.quill.focus()
      current_position = this.quill.getSelection()?.start
      unless current_position?
        current_position = this.quill.getLength()
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

        @quill.insertText @quill.getLength(), __text

        $("#mention-modal-#{@quillID}").modal("hide")

      $("#mention-modal-#{@quillID}").modal("show")

    setupEditor: (cancel_button=false) =>
      @element.html(@editordivHTML())

      if @edit_reason
        @element.before @editReasonHTML
      @element.before """<div id="mention-modal-#{@quillID}" class="modal fade"></div>"""
      @element.before """<div id="emoticon-modal-#{@quillID}" class="modal fade"></div>"""
      @element.before """<div id="image-link-modal-#{@quillID}" class="modal fade"></div>"""
      @element.before @toolbarHTML
      $("#toolbar-#{@quillID}").find(".ql-mention").click (e) =>
        do @createAndShowMentionModal
      $("#toolbar-#{@quillID}").find(".ql-emoticons").click (e) =>
        do @createAndShowEmoticonModal
      $("#toolbar-#{@quillID}").find(".ql-image-link").click (e) =>
        do @createAndShowImageLinkModal

      @element.after @dropzoneHTML
      @element.after @previewHTML
      @element.after @submitButtonHTML cancel_button

      quill = new Quill "#post-editor-#{@quillID}",
        modules:
          'link-tooltip': true
          'toolbar': { container: "#toolbar-#{@quillID}" }
        theme: 'snow'

      quill.setHTML @element.data("editor_initial_html")
      @quill = quill

      @element.data("_editor", this)
      @element.data("editor", quill)

      $("#toolbar").on 'click mousedown mousemove', (e) ->
        e.preventDefault()

      $("#dropzone-#{@quillID}").dropzone
        url: "/attach"
        dictDefaultMessage: "Click here or drop a file in to upload (image files only)."
        acceptedFiles: "image/jpeg,image/jpg,image/png,image/gif"
        maxFilesize: 30
        init: () ->
          this.on "success", (file, response) ->
            last_character = quill.getLength()
            quill.insertText last_character, "\n[attachment=#{response.attachment}:#{response.xsize}]"

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
            @saveFunction @element.data("editor").getHTML(), @element.data("editor").getText(), $("#edit-reason-#{@quillID}").val()
          else
            @saveFunction @element.data("editor").getHTML(), @element.data("editor").getText()

      $("#cancel-edit-#{@quillID}").click (e) =>
        e.preventDefault()
        if @cancelFunction?
          @cancelFunction @element.data("editor").getHTML(), @element.data("editor").getText()

      $("#preview-#{@quillID}").click (e) =>
        e.preventDefault()
        $("#preview-box-#{@quillID}").parent().show()

        $.post "/preview", JSON.stringify({text: @element.data("editor").getHTML()}), (response) =>
          $("#preview-box-#{@quillID}").html response.preview

      if @readyFunction?
        do @readyFunction

    getQuillID: () ->
      return Quill.editors.length+1

    setElementHtml: (set_html) ->
      @element.data("given_editor_initial_html", set_html)

    resetElementHtml: () ->
      if @element.data("given_editor_initial_html")?
        @element.html(@element.data("given_editor_initial_html"))
      else
        @element.html(@element.data("editor_initial_html"))

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
      do $("#edit-reason-#{@quillID}").parent().parent().remove

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

    dropzoneHTML: () =>
      return """
          <div id="dropzone-#{@quillID}" class="dropzone" style="display: none;"></div>
      """

    previewHTML: () =>
      return """
          <div class="panel panel-default" style="display: none;">
            <div class="panel-heading">Post Preview (Click Preview Button to Update)</div>
            <div id="preview-box-#{@quillID}" class="panel-body"></div>
          </div>
      """

    disableSaveButton: () =>
      $("#save-text-#{@quillID}").addClass("disabled")
      $("#upload-files-#{@quillID}").addClass("disabled")
      $("#cancel-edit-#{@quillID}").addClass("disabled")

    enableSaveButton: () =>
      $("#save-text-#{@quillID}").removeClass("disabled")
      $("#upload-files-#{@quillID}").removeClass("disabled")
      $("#cancel-edit-#{@quillID}").removeClass("disabled")

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

    editordivHTML: () =>
      return """
        <div id="post-editor-#{@quillID}" class="editor-box" style="height: #{@height};" data-placeholder=""></div>
      """

    toolbarHTML: () =>
      return """
        <div id="toolbar-#{@quillID}" class="toolbar">
          <span class="ql-format-group">
            <select title="Font" class="ql-font">
              <option value="pt_sansregular" selected>Regular</option>
              <option value="pt_sanscaption">Caption</option>
              <option value="caviar_dreams">Caviar</option>
              <option value="comic_reliefregular">Comic</option>
              <option value="droid_sans_monoregular">Monotype</option>
              <option value="monterrey">Monterrey</option>
              <option value="opensans">Open Sans</option>
            </select>
            <select title="Size" class="ql-size">
              <option value="8px">Micro</option>
              <option value="10px">Small</option>
              <option value="14px" selected>Normal</option>
              <option value="18px">Large</option>
              <option value="24px">Larger</option>
              <option value="32px">Huge</option>
            </select>
          </span>
          <span class="ql-format-group">
            <span title="Bold" class="ql-format-button ql-bold"></span>
            <span class="ql-format-separator"></span>
            <span title="Italic" class="ql-format-button ql-italic"></span>
            <span class="ql-format-separator"></span>
            <span title="Underline" class="ql-format-button ql-underline"></span>
            <span class="ql-format-separator"></span>
            <span title="Strikethrough" class="ql-format-button ql-strike"></span>
          </span>
          <span class="ql-format-group">
            <select title="Text Color" class="ql-color">
              <option value="rgb(0, 0, 0)" label="rgb(0, 0, 0)" selected></option>
              <option value="rgb(230, 0, 0)" label="rgb(230, 0, 0)"></option>
              <option value="rgb(255, 153, 0)" label="rgb(255, 153, 0)"></option>
              <option value="rgb(255, 255, 0)" label="rgb(255, 255, 0)"></option>
              <option value="rgb(0, 138, 0)" label="rgb(0, 138, 0)"></option>
              <option value="rgb(0, 102, 204)" label="rgb(0, 102, 204)"></option>
              <option value="rgb(153, 51, 255)" label="rgb(153, 51, 255)"></option>
              <option value="rgb(255, 255, 255)" label="rgb(255, 255, 255)"></option>
              <option value="rgb(250, 204, 204)" label="rgb(250, 204, 204)"></option>
              <option value="rgb(255, 235, 204)" label="rgb(255, 235, 204)"></option>
              <option value="rgb(255, 255, 204)" label="rgb(255, 255, 204)"></option>
              <option value="rgb(204, 232, 204)" label="rgb(204, 232, 204)"></option>
              <option value="rgb(204, 224, 245)" label="rgb(204, 224, 245)"></option>
              <option value="rgb(235, 214, 255)" label="rgb(235, 214, 255)"></option>
              <option value="rgb(187, 187, 187)" label="rgb(187, 187, 187)"></option>
              <option value="rgb(240, 102, 102)" label="rgb(240, 102, 102)"></option>
              <option value="rgb(255, 194, 102)" label="rgb(255, 194, 102)"></option>
              <option value="rgb(255, 255, 102)" label="rgb(255, 255, 102)"></option>
              <option value="rgb(102, 185, 102)" label="rgb(102, 185, 102)"></option>
              <option value="rgb(102, 163, 224)" label="rgb(102, 163, 224)"></option>
              <option value="rgb(194, 133, 255)" label="rgb(194, 133, 255)"></option>
              <option value="rgb(136, 136, 136)" label="rgb(136, 136, 136)"></option>
              <option value="rgb(161, 0, 0)" label="rgb(161, 0, 0)"></option>
              <option value="rgb(178, 107, 0)" label="rgb(178, 107, 0)"></option>
              <option value="rgb(178, 178, 0)" label="rgb(178, 178, 0)"></option>
              <option value="rgb(0, 97, 0)" label="rgb(0, 97, 0)"></option>
              <option value="rgb(0, 71, 178)" label="rgb(0, 71, 178)"></option>
              <option value="rgb(107, 36, 178)" label="rgb(107, 36, 178)"></option>
              <option value="rgb(68, 68, 68)" label="rgb(68, 68, 68)"></option>
              <option value="rgb(92, 0, 0)" label="rgb(92, 0, 0)"></option>
              <option value="rgb(102, 61, 0)" label="rgb(102, 61, 0)"></option>
              <option value="rgb(102, 102, 0)" label="rgb(102, 102, 0)"></option>
              <option value="rgb(0, 55, 0)" label="rgb(0, 55, 0)"></option>
              <option value="rgb(0, 41, 102)" label="rgb(0, 41, 102)"></option>
              <option value="rgb(61, 20, 102)" label="rgb(61, 20, 102)"></option>
            </select>
          </span>
          <span class="ql-format-group">
            <span title="List" class="ql-format-button ql-list"></span>
            <span class="ql-format-separator"></span>
            <span title="Bullet" class="ql-format-button ql-bullet"></span>
            <span class="ql-format-separator"></span>
            <select title="Text Alignment" class="ql-align">
              <option value="left" label="Left" selected></option>
              <option value="center" label="Center"></option>
              <option value="right" label="Right"></option>
              <option value="justify" label="Justify"></option>
            </select>
          </span>
          <span class="ql-format-group">
            <span title="Link" class="ql-format-button ql-link"></span>
            <span class="ql-format-separator"></span>
            <span title="Image" class="ql-format-button ql-image-link ql-custom-button"><span class="glyphicon glyphicon-picture"></span></span>
          </span>
          <span class="ql-format-group">
            <span class="ql-mention ql-format-button ql-custom-button">@</span>
            <span class="ql-emoticons ql-format-button ql-custom-button">&#9786;</span>
          </span>
        </div>
      """

  window.InlineEditor = InlineEditor
