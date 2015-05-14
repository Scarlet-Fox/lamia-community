$ ->
  class InlineEditor
    constructor: (element) ->
      if window.editor_is_active
        return false
      @element = $(element)
      @element.before @toolbarHTML
      @element.after @submitButtonHTML
      window.editor_is_active = true
      window.editor_initial_html = @element.html()
      @element.html(@editordivHTML())
      
      $("#post-editor").html(window.editor_initial_html)
      
      window.editor = new wysihtml5.Editor 'post-editor',
        toolbar: 'toolbar'
        parserRules:  wysihtml5ParserRules
            
    submitButtonHTML: (fullpage_option=False) ->
      if fullpage_option == true
        return """
          <div class="post-new-buttons">
            <button type="button" class="btn btn-default post-post">Save</button>
            <button type="button" class="btn btn-default post-fullpage">Full Page Editor</button>
          </div>
        """
      else
        return """
          <div class="post-new-buttons">
            <button type="button" class="btn btn-default post-post">Save</button>
          </div>
        """
    
    editordivHTML: () ->
      return """
        <div id="post-editor" data-placeholder=""></div>
      """
    
    toolbarHTML: () ->
      return """
        <div class="btn-toolbar center-block" role="toolbar" id="toolbar">
          <div class="btn-group" role="group">
            <button type="button" class="btn btn-default" data-wysihtml5-command="bold">
              <span class="glyphicon glyphicon-bold" aria-hidden="true"></span></button>
            <button type="button" class="btn btn-default" data-wysihtml5-command="italic">
              <span class="glyphicon glyphicon-italic" aria-hidden="true"></span></button>
            <button type="button" class="btn btn-default" data-wysihtml5-command="underline">
              <span class="glyphicon glyphicon-text-width" aria-hidden="true"></span></button>
          </div>
          <div class="btn-group" role="group">
            <button type="button" class="btn btn-default" data-wysihtml5-command="insertUnorderedList">
              <span class="glyphicon glyphicon-list-alt" aria-hidden="true"></span></button>
            <button type="button" class="btn btn-default" data-wysihtml5-command="insertOrderedList">
              <span class="glyphicon glyphicon-th-list" aria-hidden="true"></span></button>
          </div>
          <div class="btn-group" role="group">
            <button type="button" class="btn btn-default" data-wysihtml5-command="justifyLeft">
              <span class="glyphicon glyphicon-align-left" aria-hidden="true"></span></button>
            <button type="button" class="btn btn-default" data-wysihtml5-command="justifyCenter">
              <span class="glyphicon glyphicon-align-center" aria-hidden="true"></span></button>
            <button type="button" class="btn btn-default" data-wysihtml5-command="justifyRight">
              <span class="glyphicon glyphicon-align-right" aria-hidden="true"></span></button>
            <button type="button" class="btn btn-default" data-wysihtml5-command="justifyFull">
              <span class="glyphicon glyphicon-align-justify" aria-hidden="true"></span></button>
          </div>
          <div class="btn-group" role="group">
            <button type="button" class="btn btn-default" data-wysihtml5-command="formatBlock" data-wysihtml5-command-value="blockquote">
              <span class="glyphicon glyphicon-comment" aria-hidden="true"></span></button>
            <!-- <button type="button" class="btn btn-default" data-wysihtml5-command="">
              <span class="glyphicon glyphicon-tint" aria-hidden="true"></span></button> -->
          </div>
          <div class="btn-group" role="group">
            <button type="button" class="btn btn-default" data-wysihtml5-command="">
              <span class="glyphicon glyphicon-picture" aria-hidden="true"></span></button>
            <button type="button" class="btn btn-default" data-wysihtml5-command="">
              <span class="glyphicon glyphicon-link" aria-hidden="true"></span></button>
          </div>
        </div>
      """
      
  window.InlineEditor = InlineEditor