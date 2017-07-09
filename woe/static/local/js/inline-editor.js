// Generated by CoffeeScript 1.12.6
(function() {
  var bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

  $(function() {
    var InlineEditor;
    return InlineEditor = (function() {
      function InlineEditor(element, url, cancel_button, edit_reason, height, no_image_link) {
        if (url == null) {
          url = "";
        }
        if (cancel_button == null) {
          cancel_button = false;
        }
        if (edit_reason == null) {
          edit_reason = false;
        }
        if (height == null) {
          height = 300;
        }
        if (no_image_link == null) {
          no_image_link = false;
        }
        this.createAndShowMentionModal = bind(this.createAndShowMentionModal, this);
        this.createAndShowEmoticonModal = bind(this.createAndShowEmoticonModal, this);
        this.submitButtonHTML = bind(this.submitButtonHTML, this);
        this.editordivHTML = bind(this.editordivHTML, this);
        this.previewHTML = bind(this.previewHTML, this);
        this.dropzoneHTML = bind(this.dropzoneHTML, this);
        this.enableSaveButton = bind(this.enableSaveButton, this);
        this.disableSaveButton = bind(this.disableSaveButton, this);
        this.editReasonHTML = bind(this.editReasonHTML, this);
        this.extraButtonsHTML = bind(this.extraButtonsHTML, this);
        Dropzone.autoDiscover = false;
        this.quillID = this.getQuillID();
        this.element = $(element);
        this.edit_reason = edit_reason;
        this.height = height + "px";
        this.no_image_link = no_image_link;
        if (url !== "") {
          $.get(url, (function(_this) {
            return function(data) {
              _this.element.data("editor_initial_html", data.content);
              return _this.setupEditor(cancel_button);
            };
          })(this));
        } else {
          this.element.data("editor_initial_html", this.element.html());
          this.setupEditor(cancel_button);
        }
      }

      InlineEditor.prototype.getQuillID = function() {
        return $(".ql-editor").length + 1;
      };

      InlineEditor.prototype.onSave = function(saveFunction) {
        return this.saveFunction = saveFunction;
      };

      InlineEditor.prototype.onReady = function(readyFunction) {
        return this.readyFunction = readyFunction;
      };

      InlineEditor.prototype.onCancel = function(cancelFunction) {
        return this.cancelFunction = cancelFunction;
      };

      InlineEditor.prototype.onFullPage = function(fullPageFunction) {
        return this.fullPageFunction = fullPageFunction;
      };

      InlineEditor.prototype.noSaveButton = function() {
        return $("#save-text-" + this.quillID).remove();
      };

      InlineEditor.prototype.flashError = function(message) {
        this.element.parent().children(".alert").remove();
        return this.element.parent().prepend("<div class=\"alert alert-danger alert-dismissible fade in\" role=\"alert\">\n  <button type=\"button\" class=\"close\" data-dismiss=\"alert\" aria-label=\"Close\"><span aria-hidden=\"true\">×</span></button>\n  " + message + "\n</div>");
      };

      InlineEditor.prototype.clearEditor = function() {
        this.element.data("editor").setText("");
        return Dropzone.forElement("#dropzone-" + this.quillID).removeAllFiles();
      };

      InlineEditor.prototype.setupEditor = function(cancel_button) {
        var Block, Parchment, _this, quill, toolbar, toolbarOptions;
        if (this.edit_reason) {
          this.element.before(this.editReasonHTML);
        }
        this.element.before("<div id=\"mention-modal-" + this.quillID + "\" class=\"modal fade\"></div>");
        this.element.before("<div id=\"emoticon-modal-" + this.quillID + "\" class=\"modal fade\"></div>");
        this.element.before("<div id=\"image-link-modal-" + this.quillID + "\" class=\"modal fade\"></div>");
        this.element.html(this.editordivHTML());
        this.element.after(this.dropzoneHTML);
        this.element.after(this.previewHTML);
        this.element.after(this.submitButtonHTML(cancel_button));
        toolbarOptions = [
          ['bold', 'italic', 'underline', 'strike'], ['blockquote', 'code-block'], [
            {
              'header': 1
            }, {
              'header': 2
            }
          ], [
            {
              'list': 'ordered'
            }, {
              'list': 'bullet'
            }
          ], [
            {
              'script': 'sub'
            }, {
              'script': 'super'
            }
          ], [
            {
              'indent': '-1'
            }, {
              'indent': '+1'
            }
          ], [
            {
              'direction': 'rtl'
            }
          ], [
            {
              'size': ['small', false, 'large', 'huge']
            }
          ], [
            {
              'header': [1, 2, 3, 4, 5, 6, false]
            }
          ], [
            {
              'color': []
            }, {
              'background': []
            }
          ], [
            {
              'font': []
            }
          ], [
            {
              'align': []
            }
          ], ['clean'], ['link'], ['image']
        ];
        Parchment = Quill["import"]('parchment');
        Block = Parchment.query('block');
        Block.tagName = 'DIV';
        Quill.register(Block, true);
        quill = new Quill("#post-editor-" + this.quillID, {
          theme: 'snow',
          modules: {
            toolbar: toolbarOptions
          }
        });
        quill.clipboard.dangerouslyPasteHTML(this.element.data("editor_initial_html"));
        this.quill = quill;
        toolbar = quill.getModule('toolbar');
        _this = this;
        this.element.data("_editor", this);
        this.element.data("editor", quill);
        toolbar.addHandler('image', function() {
          var current_position;
          current_position = _this.quill.getSelection(true).index;
          $("#image-link-modal-" + _this.quillID).html("<div class=\"modal-dialog\">\n  <div class=\"modal-content\">\n    <div class=\"modal-header\">\n      <button type=\"button\" class=\"close\" data-dismiss=\"modal\" aria-label=\"Close\"><span aria-hidden=\"true\">&times;</span></button>\n      <h4 class=\"modal-title\">Paste image URL</h4>\n    </div>\n    <div class=\"modal-body\">\n      <span id=\"image-link-instructions\">Use this to insert images into your post.</span>\n      <br><br>\n      <input id=\"image-link-select\" class=\"form-control\" style=\"max-width: 100%; width: 400px;\" multiple=\"multiple\">\n      <img id=\"image-link-load\" src=\"/static/loading.gif\" style=\"display: none;\">\n    </div>\n    <div class=\"modal-footer\">\n      <button type=\"button\" class=\"btn btn-primary\" id=\"image-link-modal-insert\">Insert</button>\n      <button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Cancel</button>\n    </div>\n  </div>\n</div>");
          $("#image-link-modal-insert").click(function(e) {
            e.preventDefault();
            _this.quill.insertEmbed(current_position, 'image', $("#image-link-select").val());
            return $("#image-link-modal-" + _this.quillID).modal("hide");
          });
          return $("#image-link-modal-" + _this.quillID).modal("show");
        });
        this.element.children(".ql-toolbar").append(this.extraButtonsHTML);
        $("#add-mention-" + this.quillID).on('click', (function(_this) {
          return function(e) {
            return _this.createAndShowMentionModal();
          };
        })(this));
        $("#add-emote-" + this.quillID).on('click', (function(_this) {
          return function(e) {
            return _this.createAndShowEmoticonModal();
          };
        })(this));
        $("#toolbar-" + this.quillID).find(".ql-image-link").click((function(_this) {
          return function(e) {
            return _this.createAndShowImageLinkModal();
          };
        })(this));
        $("#dropzone-" + this.quillID).dropzone({
          url: "/attach",
          dictDefaultMessage: "Click here or drop a file in to upload (image files only).",
          acceptedFiles: "image/jpeg,image/jpg,image/png,image/gif",
          maxFilesize: 30,
          init: function() {
            return this.on("success", function(file, response) {
              return quill.insertText(quill.getSelection(true).index, "[attachment=" + response.attachment + ":" + response.xsize + "]");
            });
          }
        });
        $("#upload-files-" + this.quillID).click((function(_this) {
          return function(e) {
            e.preventDefault();
            if ($("#dropzone-" + _this.quillID).is(":visible")) {
              return $("#dropzone-" + _this.quillID).hide();
            } else {
              return $("#dropzone-" + _this.quillID).show();
            }
          };
        })(this));
        $("#save-text-" + this.quillID).click((function(_this) {
          return function(e) {
            e.preventDefault();
            if (_this.saveFunction != null) {
              if (_this.edit_reason) {
                return _this.saveFunction($("#post-editor-" + _this.quillID).children(".ql-editor").html(), _this.element.data("editor").getText(), $("#edit-reason-" + _this.quillID).val());
              } else {
                return _this.saveFunction($("#post-editor-" + _this.quillID).children(".ql-editor").html(), _this.element.data("editor").getText());
              }
            }
          };
        })(this));
        $("#cancel-edit-" + this.quillID).click((function(_this) {
          return function(e) {
            e.preventDefault();
            if (_this.cancelFunction != null) {
              return _this.cancelFunction($("#post-editor-" + _this.quillID).children(".ql-editor").html(), _this.element.data("editor").getText());
            }
          };
        })(this));
        $("#preview-" + this.quillID).click((function(_this) {
          return function(e) {
            e.preventDefault();
            $("#preview-box-" + _this.quillID).parent().show();
            return $.post("/preview", JSON.stringify({
              text: $("#post-editor-" + _this.quillID).children(".ql-editor").html()
            }), function(response) {
              $("#preview-box-" + _this.quillID).html(response.preview);
              return window.addExtraHTML("#preview-box-" + _this.quillID);
            });
          };
        })(this));
        if (this.readyFunction != null) {
          return this.readyFunction();
        }
      };

      InlineEditor.prototype.setElementHtml = function(set_html) {
        return this.element.data("given_editor_initial_html", set_html);
      };

      InlineEditor.prototype.resetElementHtml = function() {
        if (this.element.data("given_editor_initial_html") != null) {
          return this.element.html(this.element.data("given_editor_initial_html"));
        } else {
          return this.element.html(this.element.data("editor_initial_html"));
        }
      };

      InlineEditor.prototype.extraButtonsHTML = function() {
        return "<span class=\"ql-formats\">\n  <button type=\"button\" id=\"add-mention-" + this.quillID + "\" class=\"ql-mention\" >@</button>\n  <button type=\"button\" id=\"add-emote-" + this.quillID + "\" class=\"ql-mention\" >&#9786;</button>\n</span>";
      };

      InlineEditor.prototype.editReasonHTML = function() {
        return "<div class=\"form-inline\">\n  <div class=\"form-group\">\n    <label>Edit Reason: </label>\n    <input class=\"form-control\" id=\"edit-reason-" + this.quillID + "\" type=\"text\" initial=\"\"></input>\n  </div>\n</form>\n<br><br>";
      };

      InlineEditor.prototype.disableSaveButton = function() {
        $("#save-text-" + this.quillID).addClass("disabled");
        $("#upload-files-" + this.quillID).addClass("disabled");
        return $("#cancel-edit-" + this.quillID).addClass("disabled");
      };

      InlineEditor.prototype.enableSaveButton = function() {
        $("#save-text-" + this.quillID).removeClass("disabled");
        $("#upload-files-" + this.quillID).removeClass("disabled");
        return $("#cancel-edit-" + this.quillID).removeClass("disabled");
      };

      InlineEditor.prototype.dropzoneHTML = function() {
        return "<div id=\"dropzone-" + this.quillID + "\" class=\"dropzone\" style=\"display: none;\"></div>";
      };

      InlineEditor.prototype.previewHTML = function() {
        return "<div class=\"panel panel-default\" id=\"preview-container-" + this.quillID + "\" style=\"display: none;\">\n  <div class=\"panel-heading\">Post Preview (Click Preview Button to Update)</div>\n  <div id=\"preview-box-" + this.quillID + "\" class=\"panel-body\"></div>\n</div>";
      };

      InlineEditor.prototype.editordivHTML = function() {
        return "<div id=\"post-editor-" + this.quillID + "\" class=\"editor-box\" style=\"height: " + this.height + ";\" data-placeholder=\"\"></div>";
      };

      InlineEditor.prototype.submitButtonHTML = function(cancel_button) {
        if (cancel_button == null) {
          cancel_button = false;
        }
        if (cancel_button === true) {
          return "<div id=\"inline-editor-buttons-" + this.quillID + "\" class=\"inline-editor-buttons\">\n  <button type=\"button\" class=\"btn btn-default post-post\" id=\"save-text-" + this.quillID + "\">Save</button>\n  <button type=\"button\" class=\"btn btn-default post-post\" id=\"upload-files-" + this.quillID + "\">Upload Files</button>\n  <button type=\"button\" class=\"btn btn-default\" id=\"cancel-edit-" + this.quillID + "\">Cancel</button>\n  <button type=\"button\" class=\"btn btn-default\" id=\"preview-" + this.quillID + "\">Preview</button>\n</div>";
        } else {
          return "<div id=\"inline-editor-buttons-" + this.quillID + "\" class=\"inline-editor-buttons\">\n  <button type=\"button\" class=\"btn btn-default post-post\" id=\"save-text-" + this.quillID + "\">Save</button>\n  <button type=\"button\" class=\"btn btn-default post-post\" id=\"upload-files-" + this.quillID + "\">Upload Files</button>\n  <button type=\"button\" class=\"btn btn-default\" id=\"preview-" + this.quillID + "\">Preview</button>\n</div>";
        }
      };

      InlineEditor.prototype.destroyEditor = function() {
        this.element.data("editor_is_active", false);
        this.element.parent().children(".alert").remove();
        $("#inline-editor-buttons-" + this.quillID).remove();
        $("#toolbar-" + this.quillID).remove();
        $("#post-editor-" + this.quillID).remove();
        Dropzone.forElement("#dropzone-" + this.quillID).destroy();
        $("#dropzone-" + this.quillID).remove();
        $("#emoticon-modal-" + this.quillID).remove();
        $("#mention-modal-" + this.quillID).remove();
        $("#preview-container-" + this.quillID).remove();
        return $("#edit-reason-" + this.quillID).parent().parent().remove();
      };

      InlineEditor.prototype.createAndShowEmoticonModal = function() {
        var _this, current_position;
        current_position = this.quill.getSelection(true).index;
        $("#emoticon-modal-" + this.quillID).html("        <div class=\"modal-dialog\">\n          <div class=\"modal-content\">\n            <div class=\"modal-header\">\n              <button type=\"button\" class=\"close\" data-dismiss=\"modal\" aria-label=\"Close\"><span aria-hidden=\"true\">&times;</span></button>\n              <h4 class=\"modal-title\">Pick an Emote! <img src=\"/static/emoticons/fluttershy_happy_by_angelishi.gif\"></h4>\n            </div>\n            <div class=\"modal-body\">\n              <img src=\"/static/emoticons/fluttershy_happy_by_angelishi.gif\" class=\"emoticon-listing\" data-emotecode=\":)\">\n              <img src=\"/static/emoticons/fluttershy_sad_by_angelishi.gif\" class=\"emoticon-listing\" data-emotecode=\":(\">\n              <img src=\"/static/emoticons/shocked_fluttershy_by_angelishi-d7xyd7j.gif\" class=\"emoticon-listing\" data-emotecode=\":horror:\">\n              <img src=\"/static/emoticons/embarrassed_fluttershy_by_angelishi-d7xyd7k.gif\" class=\"emoticon-listing\" data-emotecode=\":shy:\">\n             <img src=\"/static/emoticons/applejack_confused_by_angelishi-d6wk2ew.gif\" class=\"emoticon-listing\" data-emotecode=\":wat:\">\n              <img src=\"/static/emoticons/nervous_aj_by_angelishi-d7ahd5y.gif\" class=\"emoticon-listing\" data-emotecode=\":S\">\n              <img src=\"/static/emoticons/liar_applejack_by_angelishi-d7aglwl.gif\" class=\"emoticon-listing\" data-emotecode=\":liarjack:\">\n              <img src=\"/static/emoticons/pinkie_laugh_by_angelishi-d6wk2ek.gif\" class=\"emoticon-listing\" data-emotecode=\":D\">\n              <img src=\"/static/emoticons/pinkie_mustache_by_angelishi-d6wk2eh.gif\" class=\"emoticon-listing\" data-emotecode=\":mustache:\">\n              <img src=\"/static/emoticons/pinkie_silly_by_angelishi-d6wk2ef.gif\" class=\"emoticon-listing\" data-emotecode=\":P\">\n              <img src=\"/static/emoticons/pinkamena_by_angelishi-d6wk2er.gif\" class=\"emoticon-listing\" data-emotecode=\":pinkamena:\">\n              <img src=\"/static/emoticons/rarity_happy_by_angelishi.gif\" class=\"emoticon-listing\" data-emotecode=\":pleased:\">\n              <img src=\"/static/emoticons/rarity_shock_2_by_angelishi-d6wk2eb.gif\" class=\"emoticon-listing\" data-emotecode=\":shocked:\">\n              <img src=\"/static/emoticons/singing_rarity_by_angelishi-d7agp33.gif\" class=\"emoticon-listing\" data-emotecode=\":sing:\">\n              <img src=\"/static/emoticons/twilight___twitch_by_angelishi.gif\" class=\"emoticon-listing\" data-emotecode=\":twitch:\">\n              <img src=\"/static/emoticons/twilight_think_by_angelishi.gif\" class=\"emoticon-listing\" data-emotecode=\":?\">\n              <img src=\"/static/emoticons/twilight_wink_by_angelishi.gif\" class=\"emoticon-listing\" data-emotecode=\";)\">\n              <img src=\"/static/emoticons/rd_yawn_by_angelishi-d9cwc1o.gif\" class=\"emoticon-listing\" data-emotecode=\":yawn:\">\n              <img src=\"/static/emoticons/rainbowdash_cool_by_angelishi.gif\" class=\"emoticon-listing\" data-emotecode=\":cool:\">\n              <img src=\"/static/emoticons/rd_laugh_by_angelishi-d7aharw.gif\" class=\"emoticon-listing\" data-emotecode=\":rofl:\">\n              <img src=\"/static/emoticons/scootaloo_want_face_by_angelishi-d7xyd7g.gif\" class=\"emoticon-listing\" data-emotecode=\":want:\">\n              <img src=\"/static/emoticons/derpy_by_angelishi-d7amv0j.gif\" class=\"emoticon-listing\" data-emotecode=\":derp:\">\n              <img src=\"/static/emoticons/head_wobble_by_angelishi-d9cwc16.gif\" class=\"emoticon-listing\" data-emotecode=\":jester:\">\n              <img src=\"/static/emoticons/love_spike_by_angelishi-d7amv0g.gif\" class=\"emoticon-listing\" data-emotecode=\":love:\">\n<br>\n              <img src=\"/static/emoticons/celestia_noapproval_by_angelishi-d9cwc1c.png\" class=\"emoticon-listing\" data-emotecode=\":unamused:\">\n              <img src=\"/static/emoticons/celestia_playful_by_angelishi-d9cwc1g.gif\" class=\"emoticon-listing\" data-emotecode=\":playful:\">\n              <img src=\"/static/emoticons/luna_please_by_angelishi-d9cwc1l.gif\" class=\"emoticon-listing\" data-emotecode=\":plz:\">\n              <img src=\"/static/emoticons/discord_troll_laugh_by_angelishi-d7xyd7m.gif\" class=\"emoticon-listing\" data-emotecode=\":troll:\">\n              <img src=\"/static/emoticons/sun_happy_by_angelishi-d6wlo5g.gif\" class=\"emoticon-listing\" data-emotecode=\":sunjoy:\">\n              <img src=\"/static/emoticons/moon_by_angelishi-d7amv0a.gif\" class=\"emoticon-listing\" data-emotecode=\":moonjoy:\">\n        <img src=\"/static/emoticons/brohoof_by_angelishi-d6wk2et.gif\" class=\"emoticon-listing\" data-emotecode=\":hoofbump:\">              </div>\n            <div class=\"modal-footer\">\n              <button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Cancel</button>\n            </div>\n          </div>\n        </div>");
        _this = this;
        $(".emoticon-listing").click(function(e) {
          var emoticon_code;
          e.preventDefault();
          emoticon_code = $(this).data("emotecode");
          _this.quill.insertText(current_position, emoticon_code);
          return $("#emoticon-modal-" + _this.quillID).modal("hide");
        });
        return $("#emoticon-modal-" + this.quillID).modal("show");
      };

      InlineEditor.prototype.createAndShowMentionModal = function() {
        $("#mention-modal-" + this.quillID).html("<div class=\"modal-dialog\">\n  <div class=\"modal-content\">\n    <div class=\"modal-header\">\n      <button type=\"button\" class=\"close\" data-dismiss=\"modal\" aria-label=\"Close\"><span aria-hidden=\"true\">&times;</span></button>\n      <h4 class=\"modal-title\">Mention Lookup</h4>\n    </div>\n    <div class=\"modal-body\">\n      Use this to insert mentions into your post.\n      <br><br>\n      <select id=\"member-select\" class=\"form-control\" style=\"max-width: 100%; width: 400px;\" multiple=\"multiple\">\n      </select>\n    </div>\n    <div class=\"modal-footer\">\n      <button type=\"button\" class=\"btn btn-primary\" id=\"mention-modal-insert\">Insert</button>\n      <button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Cancel</button>\n    </div>\n  </div>\n</div>");
        $("#member-select").select2({
          ajax: {
            url: "/user-list-api-variant",
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
        $("#mention-modal-insert").click((function(_this) {
          return function(e) {
            var __text, i, j, len, ref, val;
            e.preventDefault();
            __text = "";
            ref = $("#member-select").val();
            for (i = j = 0, len = ref.length; j < len; i = ++j) {
              val = ref[i];
              __text = __text + ("[@" + val + "]");
              if (i !== $("#member-select").val().length - 1) {
                __text = __text + ", ";
              }
            }
            _this.quill.insertText(_this.quill.getSelection(true).index, __text);
            return $("#mention-modal-" + _this.quillID).modal("hide");
          };
        })(this));
        return $("#mention-modal-" + this.quillID).modal("show");
      };

      window.InlineEditor = InlineEditor;

      return InlineEditor;

    })();
  });

}).call(this);
