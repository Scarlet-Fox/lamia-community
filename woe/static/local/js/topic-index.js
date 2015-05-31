// Generated by CoffeeScript 1.9.2
(function() {
  $(function() {
    var Topic;
    Topic = (function() {
      function Topic(slug) {
        var topic;
        this.slug = slug;
        topic = this;
        this.page = window._initial_page;
        this.max_pages = 1;
        this.pagination = window._pagination;
        this.postHTML = Handlebars.compile(this.postHTMLTemplate());
        this.paginationHTML = Handlebars.compile(this.paginationHTMLTeplate());
        this.is_mod = window._is_topic_mod;
        this.is_logged_in = window._is_logged_in;
        this.refreshPosts();
        $("nav.pagination-listing").delegate("#previous-page", "click", function(e) {
          var element;
          e.preventDefault();
          element = $(this);
          if (topic.page !== 1) {
            $(".change-page").parent().removeClass("active");
            topic.page--;
            return topic.refreshPosts();
          }
        });
        $("nav.pagination-listing").delegate("#next-page", "click", function(e) {
          var element;
          e.preventDefault();
          element = $(this);
          if (topic.page !== topic.max_pages) {
            $(".change-page").parent().removeClass("active");
            topic.page++;
            return topic.refreshPosts();
          }
        });
        $("nav.pagination-listing").delegate(".change-page", "click", function(e) {
          var element;
          e.preventDefault();
          element = $(this);
          topic.page = parseInt(element.text());
          return topic.refreshPosts();
        });
        $("nav.pagination-listing").delegate("#go-to-end", "click", function(e) {
          var element;
          e.preventDefault();
          element = $(this);
          topic.page = parseInt(topic.max_pages);
          return topic.refreshPosts();
        });
        $("nav.pagination-listing").delegate("#go-to-start", "click", function(e) {
          var element;
          e.preventDefault();
          element = $(this);
          topic.page = 1;
          return topic.refreshPosts();
        });
      }

      Topic.prototype.paginationHTMLTeplate = function() {
        return "<ul class=\"pagination\">\n  <li>\n    <a href=\"#\" aria-label=\"Start\" id=\"go-to-start\">\n      <span aria-hidden=\"true\">Go to Start</span>\n    </a>\n  </li>\n  <li>\n    <a href=\"#\" aria-label=\"Previous\" id=\"previous-page\">\n      <span aria-hidden=\"true\">&laquo;</span>\n    </a>\n  </li>\n  {{#each pages}}\n  <li><a href=\"#\" class=\"change-page page-link-{{this}}\">{{this}}</a></li>\n  {{/each}}\n  <li>\n    <a href=\"#\" aria-label=\"Next\" id=\"next-page\">\n      <span aria-hidden=\"true\">&raquo;</span>\n    </a>\n  </li>\n  <li>\n    <a href=\"#\" aria-label=\"End\" id=\"go-to-end\">\n      <span aria-hidden=\"true\">Go to End</span>\n    </a>\n  </li>\n</ul>";
      };

      Topic.prototype.postHTMLTemplate = function() {
        return "<li class=\"list-group-item post-listing-info\">\n  <div class=\"row\">\n    <div class=\"col-xs-4 hidden-md hidden-lg\">\n      <img src=\"{{user_avatar_60}}\" width=\"{{user_avatar_x_60}}\" height=\"{{user_avatar_y_60}}\" class=\"avatar-mini\">\n    </div>\n    <div class=\"col-md-3 col-xs-8\">\n      {{#if author_online}}\n      <b><span class=\"glyphicon glyphicon-ok-sign\" aria-hidden=\"true\"></span> <a href=\"/member/{{author_login_name}}\">{{author_name}}</a></b>\n      {{else}}\n      <b><span class=\"glyphicon glyphicon-minus-sign\" aria-hidden=\"true\"></span> <a href=\"/member/{{author_login_name}}\" class=\"inherit_colors\">{{author_name}}</a></b>\n      {{/if}}\n      {{#unless author_group_name}}\n      <span style=\"color:#F88379;\"><strong>Members</strong></span><br>\n      {{else}}\n      {{group_pre_html}}{{author_group_name}}{{group_post_html}}\n      {{/unless}}\n      <span class=\"hidden-md hidden-lg\">Posted {{created}}</span>\n    </div>\n    <div class=\"col-md-9 hidden-xs hidden-sm\">\n      <span id=\"post-number-1\" class=\"post-number\" style=\"vertical-align: top;\"><a href=\"{{direct_url}}\">\#{{count}}</a></span>\n      Posted {{created}}\n    </div>\n  </div>\n</li>\n<li class=\"list-group-item post-listing-post\">\n  <div class=\"row\">\n    <div class=\"col-md-3\" style=\"text-align: center;\">\n      <img src=\"{{user_avatar}}\" width=\"{{user_avatar_x}}\" height=\"{{user_avatar_y}}\" class=\"post-member-avatar hidden-xs hidden-sm\">\n      <span class=\"hidden-xs hidden-sm\"><br><br>\n      <div class=\"post-member-self-title\">{{user_title}}</div>\n        <hr></span>\n      <div class=\"post-meta\">\n      </div>\n    </div>\n    <div class=\"col-md-9 post-right\">\n      <div class=\".post-content\" id=\"post-{{_id}}\">\n        {{{html}}}\n      </div>\n      <br>\n      <div class=\"row post-edit-likes-info\">\n          <div class=\"col-md-8\">\n            {{#if _is_logged_in}}\n            <div class=\"btn-group\" role=\"group\" aria-label=\"...\">\n              <button type=\"button\" class=\"btn btn-default\">Report</button>\n              <div class=\"btn-group\">\n                <button type=\"button\" class=\"btn btn-default\">Reply</button>\n                <button type=\"button\" class=\"btn btn-default dropdown-toggle\" data-toggle=\"dropdown\" aria-expanded=\"false\">\n                  <span class=\"caret\"></span>\n                  <span class=\"sr-only\">Toggle Dropdown</span>\n                </button>\n                <ul class=\"dropdown-menu\" role=\"menu\">\n                  <li><a href=\"#\">Quote</a></li>\n                  <li><a href=\"#\">Multiquote</a></li>\n                </ul>\n              </div>\n            {{/if}}\n              <div class=\"btn-group\" style=\"\">\n                {{#if _is_topic_mod}}\n                <button type=\"button\" class=\"btn btn-default\">Options</button>\n                <button type=\"button\" class=\"btn btn-default dropdown-toggle\" data-toggle=\"dropdown\" aria-expanded=\"false\">\n                  <span class=\"caret\"></span>\n                  <span class=\"sr-only\">Toggle Dropdown</span>\n                </button>\n                <ul class=\"dropdown-menu\" role=\"menu\">\n                  <li><a href=\"#\">Edit</a></li>\n                  <li><a href=\"#\">Hide</a></li>\n                </ul>\n                {{else}}\n                  {{#if is_author}}\n                    <button type=\"button\" class=\"btn btn-default\">Options</button>\n                    <button type=\"button\" class=\"btn btn-default dropdown-toggle\" data-toggle=\"dropdown\" aria-expanded=\"false\">\n                      <span class=\"caret\"></span>\n                      <span class=\"sr-only\">Toggle Dropdown</span>\n                    </button>\n                    <ul class=\"dropdown-menu\" role=\"menu\">\n                      <li><a href=\"#\">Edit</a></li>\n                    </ul>\n                  {{/if}}\n                {{/if}}\n              </div>\n            </div>\n        </div>\n        <div class=\"col-md-4 post-likes\">\n        </div>\n      </div>\n      <hr>\n      <div class=\"post-signature\">\n      </div>\n    </div>";
      };

      Topic.prototype.refreshPosts = function() {
        var new_post_html;
        new_post_html = "";
        return $.post("/topic/" + this.slug + "/posts", JSON.stringify({
          page: this.page,
          pagination: this.pagination
        }), (function(_this) {
          return function(data) {
            var first_post, i, j, k, l, len, m, n, pages, pagination_html, post, ref, ref1, ref2, ref3, ref4, ref5, ref6, results, results1, results2, results3;
            history.pushState({
              id: "topic-page-" + _this.page
            }, '', "/topic/" + _this.slug + "/page/" + _this.page);
            first_post = ((_this.page - 1) * _this.pagination) + 1;
            ref = data.posts;
            for (i = j = 0, len = ref.length; j < len; i = ++j) {
              post = ref[i];
              post.count = first_post + i;
              post._is_topic_mod = _this.is_mod;
              post._is_logged_in = _this.is_logged_in;
              post.direct_url = "/topic/" + _this.slug + "/page/" + _this.page + "/post/" + post._id;
              new_post_html = new_post_html + _this.postHTML(post);
            }
            pages = [];
            _this.max_pages = Math.ceil(data.count / _this.pagination);
            if (_this.max_pages > 5) {
              if (_this.page > 3 && _this.page < _this.max_pages - 5) {
                pages = (function() {
                  results = [];
                  for (var k = ref1 = _this.page - 2, ref2 = _this.page + 5; ref1 <= ref2 ? k <= ref2 : k >= ref2; ref1 <= ref2 ? k++ : k--){ results.push(k); }
                  return results;
                }).apply(this);
              } else if (_this.page > 3) {
                pages = (function() {
                  results1 = [];
                  for (var l = ref3 = _this.page - 2, ref4 = _this.max_pages; ref3 <= ref4 ? l <= ref4 : l >= ref4; ref3 <= ref4 ? l++ : l--){ results1.push(l); }
                  return results1;
                }).apply(this);
              } else if (_this.page <= 3) {
                pages = (function() {
                  results2 = [];
                  for (var m = 1, ref5 = _this.page + 5; 1 <= ref5 ? m <= ref5 : m >= ref5; 1 <= ref5 ? m++ : m--){ results2.push(m); }
                  return results2;
                }).apply(this);
              }
            } else {
              pages = (function() {
                results3 = [];
                for (var n = 1, ref6 = Math.ceil(data.count / _this.pagination); 1 <= ref6 ? n <= ref6 : n >= ref6; 1 <= ref6 ? n++ : n--){ results3.push(n); }
                return results3;
              }).apply(this);
            }
            pagination_html = _this.paginationHTML({
              pages: pages
            });
            $("#topic-breadcrumb")[0].scrollIntoView();
            $(".pagination-listing").html(pagination_html);
            $("#post-container").html(new_post_html);
            return $(".page-link-" + _this.page).parent().addClass("active");
          };
        })(this));
      };

      return Topic;

    })();
    return window.topic = new Topic($("#post-container").data("slug"));
  });

}).call(this);
