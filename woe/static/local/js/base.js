// Generated by CoffeeScript 1.9.3
(function() {
  var indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

  $(function() {
    var socket;
    window.RegisterAttachmentContainer = function(selector) {
      var gifModalHTML, imgModalHTML;
      imgModalHTML = function() {
        return "<div class=\"modal-dialog\">\n  <div class=\"modal-content\">\n    <div class=\"modal-header\">\n      <button type=\"button\" class=\"close\" data-dismiss=\"modal\" aria-label=\"Close\"><span aria-hidden=\"true\">&times;</span></button>\n      <h4 class=\"modal-title\">Full Image?</h4>\n    </div>\n    <div class=\"modal-body\">\n      Would you like to view the full image? It is about <span id=\"img-click-modal-size\"></span>KB in size.\n    </div>\n    <div class=\"modal-footer\">\n      <button type=\"button\" class=\"btn btn-primary\" id=\"show-full-image\">Yes</button>\n      <button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Cancel</button>\n    </div>\n  </div>\n</div>";
      };
      gifModalHTML = function() {
        return "<div class=\"modal-dialog\">\n  <div class=\"modal-content\">\n    <div class=\"modal-header\">\n      <button type=\"button\" class=\"close\" data-dismiss=\"modal\" aria-label=\"Close\"><span aria-hidden=\"true\">&times;</span></button>\n      <h4 class=\"modal-title\">Play GIF?</h4>\n    </div>\n    <div class=\"modal-body\">\n      Would you like to play this gif image? It is about <span id=\"img-click-modal-size\"></span>KB in size.\n    </div>\n    <div class=\"modal-footer\">\n      <button type=\"button\" class=\"btn btn-primary\" id=\"show-full-image\">Play</button>\n      <button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Cancel</button>\n    </div>\n  </div>\n</div>";
      };
      $(selector).delegate(".attachment-image", "click", function(e) {
        var element, extension, size, url;
        e.preventDefault();
        element = $(this);
        if (element.data("first_click") === "yes") {
          element.attr("original_src", element.attr("src"));
          element.data("first_click", "no");
        }
        element.attr("src", element.attr("original_src"));
        if (element.data("show_box") === "no") {
          return false;
        }
        url = element.data("url");
        extension = url.split(".")[url.split(".").length - 1];
        size = element.data("size");
        $("#img-click-modal").modal('hide');
        if (extension === "gif" && parseInt(size) > 1024) {
          $("#img-click-modal").html(gifModalHTML());
          $("#img-click-modal").data("biggif", true);
          $("#img-click-modal").data("original_element", element);
          $("#img-click-modal-size").html(element.data("size"));
          return $("#img-click-modal").modal('show');
        } else {
          $("#img-click-modal").html(imgModalHTML());
          $("#img-click-modal").data("full_url", element.data("url"));
          $("#img-click-modal-size").html(element.data("size"));
          $("#img-click-modal").data("original_element", element);
          $("#img-click-modal").modal('show');
          return $("#img-click-modal").data("biggif", false);
        }
      });
      return $("#img-click-modal").delegate("#show-full-image", "click", function(e) {
        var element;
        e.preventDefault();
        if (!$("#img-click-modal").data("biggif")) {
          window.open($("#img-click-modal").data("full_url"), "_blank");
          return $("#img-click-modal").modal('hide');
        } else {
          element = $("#img-click-modal").data("original_element");
          element.attr("src", element.attr("src").replace(".gif", ".animated.gif"));
          return $("#img-click-modal").modal('hide');
        }
      });
    };
    socket = io.connect('http://' + document.domain + ':3000' + '');
    socket.on("notify", function(data) {
      var _html, count, counter_element, notification_listing, notifications_listed, ref;
      if (ref = window.woe_is_me, indexOf.call(data.users, ref) >= 0) {
        counter_element = $("#notification-counter");
        count = parseInt(counter_element.text()) + 1;
        counter_element.text(count);
        notification_listing = $("#notification-listing");
        notifications_listed = $("a.notification-link");
        if (notifications_listed.length > 14) {
          notifications_listed[notifications_listed.length - 1].remove();
        }
        _html = "<a href=\"" + data.url + "\" data-notification=\"" + data.id + "\" class=\"notification-link\">" + data.title + "</a>";
        if (notifications_listed.length === 0) {
          return $("#notification-dropdown").append(_html);
        } else {
          return $(notifications_listed[0]).before(_html);
        }
      }
    });
    $(".post-link").click(function(e) {
      e.preventDefault();
      return $.post($(this).attr("href"), function(data) {
        return window.location = data.url;
      });
    });
    $("#notification-dropdown").delegate(".notification-link", "click", function(e) {
      e.preventDefault();
      return $.post("/dashboard/ack_notification", JSON.stringify({
        notification: $(this).data("notification")
      }), (function(_this) {
        return function(data) {
          return window.location = $(_this).attr("href");
        };
      })(this));
    });
    window.setupContent = function() {
      return window.addExtraHTML("body");
    };
    window.addExtraHTML = function(selector) {
      $(selector).find(".content-spoiler").before("<a class=\"btn btn-info btn-xs toggle-spoiler\">Toggle Spoiler</a>");
      $(selector).find(".toggle-spoiler").click(function(e) {
        var spoiler;
        spoiler = $(this).next(".content-spoiler");
        if (spoiler.is(":visible")) {
          return spoiler.hide();
        } else {
          return spoiler.show();
        }
      });
      return $(selector).find("blockquote").each(function() {
        var element, time;
        element = $(this);
        time = moment.unix(element.data("time")).format("MMMM Do YYYY @ h:mm:ss a");
        if (time !== "Invalid date") {
          if (element.data("link") != null) {
            return element.prepend("<p>On " + time + ", <a href=\"\">" + (element.data("author")) + " said:</a></p>");
          } else {
            return element.prepend("<p>On " + time + ", " + (element.data("author")) + " said:</p>");
          }
        }
      });
    };
  });

}).call(this);