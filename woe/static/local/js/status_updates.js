// Generated by CoffeeScript 1.9.2
(function() {
  $(function() {
    var Status, s;
    Status = (function() {
      function Status() {
        this.id = $("#status").attr("data-id");
      }

      Status.prototype.addReply = function() {
        return $.post("/status/" + this.id + "/", {
          text: $("#status-reply")[0].value
        }, function(response) {
          return console.log(response);
        });
      };

      return Status;

    })();
    s = new Status;
    return $("#submit-reply").click(function(e) {
      e.preventDefault();
      return s.addReply();
    });
  });

}).call(this);
