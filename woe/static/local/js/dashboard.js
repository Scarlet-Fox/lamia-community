// Generated by CoffeeScript 1.9.3
(function() {
  var indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

  $(function() {
    var Dashboard;
    Dashboard = (function() {
      function Dashboard() {
        var _panel, socket;
        this.categories = {};
        this.notificationTemplate = Handlebars.compile(this.notificationHTML());
        this.panelTemplate = Handlebars.compile(this.panelHTML());
        this.dashboard_container = $("#dashboard-container");
        this.category_names = {
          topic: "Topics",
          pm: "Private Messages",
          mention: "Mentioned",
          topic_reply: "Topic Replies",
          boop: "Boops",
          mod: "Moderation",
          status: "Status Updates",
          new_member: "New Members",
          announcement: "Announcements",
          profile_comment: "Profile Comments",
          rules_updated: "Rule Update",
          faqs: "FAQs Updated",
          user_activity: "Followed:User Activity",
          streaming: "Streaming",
          other: "Other"
        };
        this.buildDashboard();
        _panel = this;
        socket = io.connect('http://' + document.domain + ':3000' + '');
        socket.on("notify", function(data) {
          var ref;
          if (ref = window.woe_is_me, indexOf.call(data.users, ref) >= 0) {
            _panel.addToPanel(data, true);
            return _panel.setPanelDates();
          }
        });
        $("#dashboard-container").delegate(".ack_all", "click", function(e) {
          var panel;
          e.preventDefault();
          panel = $("#" + $(this).data("panel"));
          return $.post("/dashboard/ack_category", JSON.stringify({
            category: panel.attr("id")
          }), (function(_this) {
            return function(data) {
              if (data.success != null) {
                panel.remove();
                return _panel.isPanelEmpty();
              }
            };
          })(this));
        });
        $("#dashboard-container").delegate(".ack_single", "click", function(e) {
          var notification, panel, panel_notifs;
          e.preventDefault();
          notification = $("#" + $(this).data("notification"));
          panel_notifs = $("#notifs-" + $(this).data("panel"));
          panel = $("#" + $(this).data("panel"));
          return $.post("/dashboard/ack_notification", JSON.stringify({
            notification: notification.attr("id")
          }), (function(_this) {
            return function(data) {
              if (data.success != null) {
                if (panel_notifs.children().length < 2) {
                  panel.remove();
                  return _panel.isPanelEmpty();
                } else {
                  notification.remove();
                  return _panel.isPanelEmpty();
                }
              }
            };
          })(this));
        });
      }

      Dashboard.prototype.isPanelEmpty = function() {
        if ($(".dashboard-panel").length === 0) {
          return $("#dashboard-container").html("<p class=\"nothing-new\">No new notifications, yet.</p>");
        } else {
          return $(".nothing-new").remove();
        }
      };

      Dashboard.prototype.setPanelDates = function() {
        return $(".dashboard-panel").children(".panel").children("ul").each(function() {
          var element, first_timestamp;
          element = $(this);
          first_timestamp = element.children("li").first().data("stamp");
          return element.parent().parent().data("stamp", first_timestamp);
        });
      };

      Dashboard.prototype.addToPanel = function(notification, live) {
        var category_element, count, existing_notification, panel, ref;
        if (live == null) {
          live = false;
        }
        category_element = $("#notifs-" + notification.category);
        if (category_element.length === 0) {
          panel = {
            panel_id: notification.category,
            panel_title: this.category_names[notification.category]
          };
          this.dashboard_container.append(this.panelTemplate(panel));
          category_element = $("#notifs-" + notification.category);
        }
        if (!live) {
          if (((ref = notification.content) != null ? ref._ref : void 0) != null) {
            notification.reference = notification.content._ref;
          } else {
            notification.reference = "";
          }
        }
        existing_notification = $(".ref-" + notification.reference + "-" + notification.category);
        if (existing_notification.length > 0 && notification.reference !== "") {
          count = parseInt(existing_notification.data("count"));
          count = count + 1;
          if (!existing_notification.children("media-left").is(":visible")) {
            existing_notification.children(".media-left").show();
          }
          existing_notification.data("count", count);
          existing_notification.data("stamp", notification.stamp);
          existing_notification.children(".media-left").children(".badge").text(count);
          existing_notification.find(".m-name").attr("href", "/members/" + notification.member_name);
          existing_notification.find(".m-name").text(notification.member_disp_name);
          existing_notification.find(".m-time").text(notification.time);
          existing_notification.find(".m-title").text(notification.text);
          return existing_notification.find(".m-title").attr("href", notification.url);
        } else {
          if (live) {
            return category_element.prepend(this.notificationTemplate(notification));
          } else {
            return category_element.append(this.notificationTemplate(notification));
          }
        }
      };

      Dashboard.prototype.buildDashboard = function() {
        return $.post("/dashboard/notifications", {}, (function(_this) {
          return function(response) {
            var i, len, notification, ref;
            ref = response.notifications;
            for (i = 0, len = ref.length; i < len; i++) {
              notification = ref[i];
              _this.addToPanel(notification);
            }
            _this.isPanelEmpty();
            return _this.setPanelDates();
          };
        })(this));
      };

      Dashboard.prototype.notificationHTML = function() {
        return "<li class=\"list-group-item ref-{{reference}}-{{category}}\" id=\"{{_id}}\" data-stamp=\"{{stamp}}\" data-count=\"1\">\n  <div class=\"media-left\" style=\"display: none;\"><span class=\"badge\"></span></div>\n  <div class=\"media-body\">\n    <a href=\"{{url}}\" class=\"m-title\">{{text}}</a><button class=\"close ack_single\" data-notification=\"{{_id}}\" data-panel=\"{{category}}\">&times;</button>\n    <p class=\"text-muted\"> by <a href=\"/members/{{member_name}}\" class=\"m-name\">{{member_disp_name}}</a> - <span class=\"m-time\">{{time}}</span></p>\n  </div>\n</li>";
      };

      Dashboard.prototype.panelHTML = function() {
        return "<div class=\"col-sm-6 col-md-4 dashboard-panel\" id=\"{{panel_id}}\">\n  <div class=\"panel panel-default\">\n    <div class=\"panel-heading\">\n      <span>{{panel_title}}</span>\n      <button class=\"close ack_all\" data-panel=\"{{panel_id}}\">&times;</button>\n    </div>\n    <ul class=\"list-group panel-body\" id=\"notifs-{{panel_id}}\">\n    </ul>\n  </div>\n</div>";
      };

      return Dashboard;

    })();
    return window.woeDashboard = new Dashboard;
  });

}).call(this);
