// Generated by CoffeeScript 1.10.0
(function() {
  $(function() {
    var NewTopic;
    window.onbeforeunload = function() {
      if (!window.save) {
        return "You haven't saved your changes.";
      }
    };
    NewTopic = (function() {
      function NewTopic(slug) {
        var new_topic;
        this.slug = slug;
        this.inline_editor = new InlineEditor("#new-post-box", "", false);
        this.meta = {};
        this.poll = {};
        new_topic = self;
        this.inline_editor.onSave(function(html, text) {
          var meta, poll, prefix, title;
          window.save = true;
          title = $("#title").val();
          prefix = $("#prefix").val();
          meta = new_topic.meta;
          poll = new_topic.poll;
          return $.post("/category/" + slug + "/new-topic", JSON.stringify({
            html: html,
            text: text,
            meta: meta,
            title: title,
            prefix: prefix,
            poll: poll
          }), (function(_this) {
            return function(data) {
              if (data.error != null) {
                return topic.inline_editor.flashError(data.error);
              } else {
                return window.location = data.url;
              }
            };
          })(this));
        });
      }

      return NewTopic;

    })();
    return window.topic = new NewTopic($("#new-topic-form").data("slug"));
  });

}).call(this);
