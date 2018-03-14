// Generated by CoffeeScript 1.12.6
(function() {
  $(function() {
    var _option, author, category, i, j, k, len, len1, len2, max_pages, page, paginationForPostsHTMLTemplate, paginationForPostsTemplate, paginationHTMLTemplate, paginationTemplate, ref, ref1, ref2, resultTemplate, resultTemplateHTML, topic, updateSearch;
    $(".variable-option").hide();
    $(".posts-option").show();
    page = 1;
    max_pages = 1;
    $("#start-date").datepicker({
      format: "m/d/yy",
      clearBtn: true
    });
    $("#end-date").datepicker({
      format: "m/d/yy",
      clearBtn: true
    });
    $("#content-search").change(function(e) {
      var content_type;
      content_type = $(this).val();
      if (content_type === "posts") {
        $(".variable-option").hide();
        return $(".posts-option").show();
      } else if (content_type === "topics") {
        $(".variable-option").hide();
        return $(".topics-option").show();
      } else if (content_type === "status") {
        return $(".variable-option").hide();
      } else if (content_type === "blogs") {
        $(".variable-option").hide();
        return $(".blogs-option").show();
      } else if (content_type === "messages") {
        $(".variable-option").hide();
        return $(".messages-option").show();
      }
    });
    if (window.authors.length > 0) {
      ref = window.authors;
      for (i = 0, len = ref.length; i < len; i++) {
        author = ref[i];
        _option = "<option value=\"" + author.id + "\" selected=\"selected\">" + author.text + "</option>";
        $("#author-select").append(_option);
      }
    }
    $("#author-select").select2({
      ajax: {
        url: "/user-list-api",
        dataType: 'json',
        delay: 250,
        data: function(params) {
          return {
            q: params.term
          };
        },
        processResults: function(data, page) {
          console.log({
            results: data.results
          });
          return {
            results: data.results
          };
        },
        cache: true
      },
      minimumInputLength: 2
    });
    if (window.categories.length > 0) {
      ref1 = window.categories;
      for (j = 0, len1 = ref1.length; j < len1; j++) {
        category = ref1[j];
        _option = "<option value=\"" + category.id + "\" selected=\"selected\">" + category.text + "</option>";
        $("#category-select").append(_option);
      }
    }
    if (window.topics.length > 0) {
      ref2 = window.topics;
      for (k = 0, len2 = ref2.length; k < len2; k++) {
        topic = ref2[k];
        _option = "<option value=\"" + topic.id + "\" selected=\"selected\">" + topic.text + "</option>";
        if (window.content_type === "posts") {
          $("#topic-select").append(_option);
        } else {
          $("#pm-topic-select").append(_option);
        }
      }
    }
    $("#topic-select").select2({
      ajax: {
        url: "/topic-list-api",
        dataType: 'json',
        delay: 250,
        data: function(params) {
          return {
            q: params.term
          };
        },
        processResults: function(data, page) {
          console.log({
            results: data.results
          });
          return {
            results: data.results
          };
        },
        cache: true
      },
      minimumInputLength: 2
    });
    $("#category-select").select2({
      ajax: {
        url: "/category-list-api",
        dataType: 'json',
        delay: 250,
        data: function(params) {
          return {
            q: params.term
          };
        },
        processResults: function(data, page) {
          console.log({
            results: data.results
          });
          return {
            results: data.results
          };
        },
        cache: true
      },
      minimumInputLength: 2
    });
    $("#blog-select").select2({
      ajax: {
        url: "/blog-list-api",
        dataType: 'json',
        delay: 250,
        data: function(params) {
          return {
            q: params.term
          };
        },
        processResults: function(data, page) {
          console.log({
            results: data.results
          });
          return {
            results: data.results
          };
        },
        cache: true
      },
      minimumInputLength: 2
    });
    $("#pm-topic-select").select2({
      ajax: {
        url: "/pm-topic-list-api",
        dataType: 'json',
        delay: 250,
        data: function(params) {
          return {
            q: params.term
          };
        },
        processResults: function(data, page) {
          console.log({
            results: data.results
          });
          return {
            results: data.results
          };
        },
        cache: true
      },
      minimumInputLength: 2
    });
    $("#search-for").val(window.search_for);
    $("#content-search").val(window.content_type);
    $("#start-date").val(window.start_date);
    $("#end-date").val(window.end_date);
    resultTemplateHTML = function() {
      return "<ul class=\"list-group\">\n  <li class=\"list-group-item\">\n    <p>\n      <b>\n        <a href=\"{{url}}\" class=\"search-result-title\">{{title}}</a>\n      </b>\n    </p>\n    <div class=\"search-result-content\">\n        {{{description}}}\n        {{#if readmore}}\n        <a href=\"{{url}}\" class=\"readmore\">\n          <br><b>Read more »</b><br>\n        </a>\n        {{/if}}\n    </div>\n    <p class=\"text-muted\">by <a class=\"hover_user\" href=\"/member/{{author_profile_link}}\">{{author_name}}</a> - <a href=\"{{url}}\">{{time}}</a>\n    </p>\n  </li>\n</ul>";
    };
    resultTemplate = Handlebars.compile(resultTemplateHTML());
    paginationForPostsHTMLTemplate = function() {
      return "<ul class=\"pagination\">\n  <li>\n    <a href=\"\" aria-label=\"Previous\" class=\"previous-page\">\n      <span aria-hidden=\"true\">Previous Page</span>\n    </a>\n  </li>\n  <li>\n    <a href=\"\" aria-label=\"Next\" class=\"next-page\">\n      <span aria-hidden=\"true\">Next Page</span>\n    </a>\n  </li>\n</ul>";
    };
    paginationForPostsTemplate = Handlebars.compile(paginationForPostsHTMLTemplate());
    paginationHTMLTemplate = function() {
      return "<ul class=\"pagination\">\n  <li>\n    <a href=\"\" aria-label=\"Start\" class=\"go-to-start\">\n      <span aria-hidden=\"true\">Go to Start</span>\n    </a>\n  </li>\n  <li>\n    <a href=\"\" aria-label=\"Previous\" class=\"previous-page\">\n      <span aria-hidden=\"true\">&laquo;</span>\n    </a>\n  </li>\n  {{#each pages}}\n  <li><a href=\"\" class=\"change-page page-link-{{this}}\">{{this}}</a></li>\n  {{/each}}\n  <li>\n    <a href=\"\" aria-label=\"Next\" class=\"next-page\">\n      <span aria-hidden=\"true\">&raquo;</span>\n    </a>\n  </li>\n  <li>\n    <a href=\"\" aria-label=\"End\" class=\"go-to-end\">\n      <span aria-hidden=\"true\">Go to End</span>\n    </a>\n  </li>\n</ul>";
    };
    paginationTemplate = Handlebars.compile(paginationHTMLTemplate());
    updateSearch = function() {
      var content_type, data;
      content_type = $("#content-search").val();
      data = {
        q: $("#search-for").val(),
        content_type: content_type,
        page: page,
        authors: $("#author-select").val()
      };
      if ($("#start-date").val() !== "") {
        data["start_date"] = $("#start-date").val();
      }
      if ($("#end-date").val() !== "") {
        data["end_date"] = $("#end-date").val();
      }
      if (content_type === "messages") {
        data["topics"] = $("#pm-topic-select").val();
      }
      if (content_type === "posts") {
        data["topics"] = $("#topic-select").val();
      }
      if (content_type === "topics") {
        data["categories"] = $("#category-select").val();
      }
      if (content_type === "blogs") {
        data["blogs"] = $("#blog-select").val();
      }
      $("#search-results").hide();
      $("#search-spinner").show();
      $("#results-header").text("Searching...");
      return $.post("/search", JSON.stringify(data), function(data) {
        var _html, l, len3, m, n, o, p, pages, pagination_html, ref3, ref4, ref5, ref6, ref7, ref8, result, results, results1, results2, results3;
        console.log(data);
        if (data.count + 0 === 0) {
          $("#search-results-buffer").html("");
          $("#search-results").html("<h3>No results...</h3><br><br>");
          $("#search-spinner").hide();
          $("#search-results").show();
          pagination_html = paginationTemplate({
            pages: 0
          });
          $("#results-header")[0].scrollIntoView();
          $(".search-pagination").html(pagination_html);
          return $("#results-header").text(data.count + " Search Results");
        } else {
          _html = "";
          ref3 = data.results;
          for (l = 0, len3 = ref3.length; l < len3; l++) {
            result = ref3[l];
            _html = _html + resultTemplate(result).replace("img", "i");
          }
          $("#search-results-buffer").html(_html);
          $("#search-results-buffer").find("br").remove();
          $("#search-spinner").hide();
          $("#search-results").show();
          $("#search-results").html($("#search-results-buffer").html());
          $("#search-results-buffer").html("");
          $(".search-result-content").dotdotdot({
            height: 200,
            after: ".readmore"
          });
          if ($("#content-search").val() !== "posts") {
            pages = [];
            max_pages = Math.ceil(data.count / data.pagination);
            if (max_pages > 5) {
              if (page > 3 && page < max_pages - 5) {
                pages = (function() {
                  results = [];
                  for (var m = ref4 = page - 2, ref5 = page + 5; ref4 <= ref5 ? m <= ref5 : m >= ref5; ref4 <= ref5 ? m++ : m--){ results.push(m); }
                  return results;
                }).apply(this);
              } else if (page > 3) {
                pages = (function() {
                  results1 = [];
                  for (var n = ref6 = page - 2; ref6 <= max_pages ? n <= max_pages : n >= max_pages; ref6 <= max_pages ? n++ : n--){ results1.push(n); }
                  return results1;
                }).apply(this);
              } else if (page <= 3) {
                pages = (function() {
                  results2 = [];
                  for (var o = 1, ref7 = page + 5; 1 <= ref7 ? o <= ref7 : o >= ref7; 1 <= ref7 ? o++ : o--){ results2.push(o); }
                  return results2;
                }).apply(this);
              }
            } else {
              pages = (function() {
                results3 = [];
                for (var p = 1, ref8 = Math.ceil(data.count / data.pagination); 1 <= ref8 ? p <= ref8 : p >= ref8; 1 <= ref8 ? p++ : p--){ results3.push(p); }
                return results3;
              }).apply(this);
            }
            pagination_html = paginationTemplate({
              pages: pages
            });
          } else {
            pagination_html = paginationForPostsHTMLTemplate;
          }
          $("#results-header")[0].scrollIntoView();
          $(".search-pagination").html(pagination_html);
          $(".search-pagination").show();
          if ($("#content-search").val() !== "posts") {
            $("#results-header").text(data.count + " Search Results");
          } else {
            $("#results-header").text("Search Results");
            if (data.count === 20) {
              $(".next-page").hide();
              max_pages = page;
            } else {
              $(".next-page").show();
              max_pages = page + 1;
            }
            console.log(page);
            if (page === 1) {
              $(".previous-page").hide();
            } else {
              $(".previous-page").show();
            }
          }
          return $(".page-link-" + page).parent().addClass("active");
        }
      });
    };
    $("#search").click(function(e) {
      e.preventDefault();
      page = 1;
      $(".search-pagination").hide();
      return updateSearch();
    });
    $("form").submit(function(e) {
      e.preventDefault();
      return $("#search").click();
    });
    $(".search-pagination").delegate(".next-page", "click", function(e) {
      var element;
      e.preventDefault();
      element = $(this);
      if (page !== max_pages) {
        $(".change-page").parent().removeClass("active");
        page++;
        return updateSearch();
      }
    });
    $(".search-pagination").delegate(".previous-page", "click", function(e) {
      var element;
      e.preventDefault();
      element = $(this);
      if (page !== 1) {
        $(".change-page").parent().removeClass("active");
        page--;
        return updateSearch();
      }
    });
    $(".search-pagination").delegate(".go-to-end", "click", function(e) {
      var element;
      e.preventDefault();
      element = $(this);
      page = parseInt(max_pages);
      return updateSearch();
    });
    $(".search-pagination").delegate(".change-page", "click", function(e) {
      var element;
      e.preventDefault();
      element = $(this);
      page = parseInt(element.text());
      return updateSearch();
    });
    return $(".search-pagination").delegate(".go-to-start", "click", function(e) {
      var element;
      e.preventDefault();
      element = $(this);
      page = 1;
      return updateSearch();
    });
  });

}).call(this);
