odoo.define('ks_theme_kinetik.ks_video_snippts', function(require) {
    "use strict";
      var session = require('web.session');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Widget = require('web.Widget');
    var ks_widget = require('web_editor.widget');
    var animation = require('website.content.snippets.animation');
    var core = require('web.core');
    var website = require('website.utils');
    var options = require('web_editor.snippets.options');
    var ks_website_slider = require('ks_ecommerce_theme.product_multi_slider_base');
    var _t = core._t;
    var QWeb = core.qweb;
    var data_global
    var data_1
    var attachment_id
    var qweb_modal = ajax.loadXML('/ks_theme_kinetik/static/src/xml/ks_attach.xml',QWeb);
    var ks_SnippetSelectionDialog = ks_widget.Dialog.extend({
     start: function() {
             var ks_self = this;
             ks_self.ks_setData(ks_self);
             ks_self._super();
        },
         ks_setData:function(modal){
         var modal_html =  $(QWeb.render('ks_theme_kinetik.ks_video_selection', {}));
         $(modal.$el).append(modal_html);
            $(document).on('click','.ks_chatter_input',function(ev){
                $('.ks_chatter_input').on('change',function(ev){
                     data_global= {
                        'name': ev.currentTarget.files[0].name,
                        'file': ev.currentTarget.files[0],
                     };
                })
            })
        },
    })
    options.registry.video_actions = options.Class.extend({
        on_prompt:function(ks_self){
                var dialog = new ks_SnippetSelectionDialog(ks_self, {
                    title: _t('Select Video'),
                });
                dialog.open();
                dialog.on('save', this, function () {
                     data_1 = {}
                     data_1 = {
                        'video_message' : $('.ks_message_video').val(),
                        'button_message' : $('.ks_message_button').val(),
                        'button_url' : $('.ks_url_button').val()
                        }
                        if(!_.isEmpty(data_global)){
                                 var ext = data_global['name'].split('.').pop().toLowerCase();
                                  if($.inArray(ext, ['mp4','3gp','webm']) !== -1) {
                                            ajax.post('/product_video/data/create', data_global).then(function(attachment){
                                            var ks_new_slider = new animation.registry.ks_video_snippet(ks_self);
                                            ks_new_slider.start(attachment.id,data_1,ks_self);
                                            }.bind(this))
                                  }
                                   else{
                                         alert('Invalid extension!');
                                         data_global={}
                                     }

                        }
                        else{
                             alert('Please select a video');
                        }

                });
                dialog.on('cancel', this,function () {
                       this.$target.remove();
                });

        },
        onBuilt: function() {
                var ks_self = this;
                ks_self.on_prompt(ks_self)
                return this._super();
            },
       cleanForSave: function() {
            this.$target.empty();
        },
    });

    })