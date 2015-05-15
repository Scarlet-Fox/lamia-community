$ ->
  class InlineEditor
    constructor: (element, fullpage_option=false) ->
      @quillID = do @getQuillID  
      @element = $(element)
      if @element.data("editor_is_active")
        return false
      @element.data("editor_is_active", true)
      @element.data("editor_initial_html", @element.html())
      @element.html(@editordivHTML())
      
      @element.before @toolbarHTML
      @element.after @submitButtonHTML fullpage_option
      
      $("#post-editor-#{@quillID}").html(@element.data("editor_initial_html"))
      
      quill = new Quill "#post-editor-#{@quillID}", 
        modules:
          'link-tooltip': true
          'toolbar': { container: "#toolbar-#{@quillID}" }
      
      @element.data("editor", quill)
      
      $("#save-text-#{@quillID}").click (e) =>
        e.preventDefault()
        if @saveFunction?
          @saveFunction @element.data("editor").getHTML()
        
      $("#cancel-edit-#{@quillID}").click (e) =>
        e.preventDefault()
        if @cancelFunction?
          @cancelFunction @element.data("editor").getHTML()
    
    getQuillID: () ->
      return Quill.editors.length+1
    
    resetElementHtml: () ->
      @element.html(@element.data("editor_initial_html"))
    
    onSave: (saveFunction) ->
      @saveFunction = saveFunction
    
    onCancel: (cancelFunction) ->
      @cancelFunction = cancelFunction
    
    onFullPage: (fullPageFunction) ->
      @fullPageFunction = fullPageFunction
    
    destroyEditor: () ->
      @element.data("editor_is_active", false)
      do $("#inline-editor-buttons-#{@quillID}").remove
      do $("#toolbar-#{@quillID}").remove
      do $("#post-editor-#{@quillID}").remove
    
    submitButtonHTML: (fullpage_option=False) =>
      if fullpage_option == true
        return """
          <div id="inline-editor-buttons-#{@quillID}" class="inline-editor-buttons">
            <button type="button" class="btn btn-default post-post" id="save-text-#{@quillID}">Save</button>
            <button type="button" class="btn btn-default" id="cancel-edit-#{@quillID}">Cancel</button>
            <button type="button" class="btn btn-default" id="fullpage-edit-#{@quillID}">Full Page Editor</button>
          </div>
        """
      else
        return """
          <div id="inline-editor-buttons-#{@quillID}" class="inline-editor-buttons">
            <button type="button" class="btn btn-default" id="save-text-#{@quillID}">Save</button>
            <button type="button" class="btn btn-default" id="cancel-edit-#{@quillID}">Cancel</button>
          </div>
        """
    
    editordivHTML: () =>
      return """
        <div id="post-editor-#{@quillID}" class="editor-box" data-placeholder=""></div>
      """
    
    toolbarHTML: () =>
      return """
        <div class="btn-toolbar" role="toolbar" id="toolbar-#{@quillID}">
          <div class="btn-group" role="group">
            <button type="button" class="btn btn-default ql-bold"><b>b</b></button>
            <button type="button" class="btn btn-default ql-italic"><i>i</i></button>
            <button type="button" class="btn btn-default ql-underline"><u>u</u></button>
            <button type="button" class="btn btn-default ql-strike"><s>s</s></button>
          </div>
          <div class="btn-group" role="group">
            <button type="button" class="btn btn-default ql-link">url</button>
          </div>
        </div>
      """
      
  window.InlineEditor = InlineEditor