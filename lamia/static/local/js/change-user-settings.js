// Generated by CoffeeScript 1.12.7
(function() {
  $(function() {
    $(".notification-toggle").click(function(e) {
      var _data, category, element, method, on_or_off;
      element = $(this);
      category = element.data("target");
      method = element.data("method");
      on_or_off = element.is(":checked");
      _data = {
        category: category,
        method: method,
        on_or_off: on_or_off
      };
      return $.post("/member/" + window.l_name + "/toggle-notification-method", JSON.stringify(_data), (function(_this) {
        return function(data) {
          return console.log(data);
        };
      })(this));
    });
    $("#add-user-field").click(function(e) {
      var field, field_box, value;
      e.preventDefault();
      field_box = $($(".fields")[0]);
      field = $("#user-field-select").val();
      value = $("#user-field-value").val();
      if (!field_box.is(":visible")) {
        field_box.show();
      }
      field_box.children("ul").append("<li><strong>" + field + "</strong>&nbsp;&nbsp;&nbsp;" + value + "</li>");
      return $.post("/member/" + window.l_name + "/add-user-field", JSON.stringify({
        field: field,
        value: value
      }), (function(_this) {
        return function(data) {
          return console.log;
        };
      })(this));
    });
    $(".remove-user-field").click(function(e) {
      var element, field, value;
      e.preventDefault();
      element = $(this);
      field = element.data("field");
      value = element.data("value");
      element.parent().remove();
      return $.post("/member/" + window.l_name + "/remove-user-field", JSON.stringify({
        field: field,
        value: value
      }), (function(_this) {
        return function(data) {
          return console.log;
        };
      })(this));
    });
    $("#user-ignore-select").select2({
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
    $("#birthday").datepicker({
      format: "m/d/yyyy",
      clearBtn: true
    });
    return $("#user-ignore-button").click(function(e) {
      var data;
      e.preventDefault();
      data = $("#user-ignore-select").val();
      return $.post("/member/" + window.l_name + "/ignore-users", JSON.stringify({
        data: data
      }), (function(_this) {
        return function(data) {
          return window.location = data.url;
        };
      })(this));
    });
  });

}).call(this);