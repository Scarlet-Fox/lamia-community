// Generated by CoffeeScript 1.12.7
(function() {
  $(function() {
    var blog_comment_editor;
    blog_comment_editor = new InlineEditor("#blog-comment");
    blog_comment_editor.noSaveButton();
    window.onbeforeunload = function() {
      if (!window.save) {
        return "You haven't saved your changes.";
      }
    };
    return $("form").submit(function(e) {
      window.save = true;
      $("#comment").val(blog_comment_editor.getHTML());
      return true;
    });
  });

}).call(this);