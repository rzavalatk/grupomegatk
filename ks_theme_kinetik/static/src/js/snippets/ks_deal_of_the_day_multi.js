odoo.define('ks_theme_kinetik.ks_deal_of_the_days', function(require) {
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
    var qweb_modal = ajax.loadXML('/ks_theme_kinetik/static/src/xml/ks_deal_of_the_day.xml',QWeb);
    var ks_SnippetSelectionDialog = ks_widget.Dialog.extend({
     start: function() {
             var ks_self = this;
             ks_self.ks_setData(ks_self);
             ks_self._super();
        },
         ks_setData:function(modal){
         var modal_html =  $(QWeb.render('ks_theme_kinetik.ks_deal_of_the_day_selection', {}));
         $(modal.$el).append(modal_html);
        },
    })
    options.registry.deal_actions = options.Class.extend({
        on_prompt:function(ks_self){
                var dialog = new ks_SnippetSelectionDialog(ks_self, {
                    title: _t('Select Date'),
                });
                dialog.open();
                dialog.on('save', this, function () {
                     data_1 = {}
                     data_1 = {
                        'date_start' : $('.ks_start_date').val(),
                        'date_end' : $('.ks_end_date').val(),
                        'button_message' : $('.ks_message_button').val(),
                        'button_url' : $('.ks_url_button').val()
                        }
                        if(!_.isEmpty(data_1['date_start']) && !_.isEmpty(data_1['date_end'])){
                            ajax.post('/deal_of_day/data/second/create', data_1).then(function(seconds){
                            if(seconds.seconds){
                                var ks_new_slider = new animation.registry.ks_deal_of_the_day_snippet(ks_self);
                                ks_new_slider.start(data_1,ks_self);
                            }
                            else{
                                ks_self.$target.parents().eq(3).remove();
                                alert('Please select a  valid start date');
                            }
                             }.bind(this))
                        }
                        else if(!_.isEmpty(data_1['date_start'])){
                             ks_self.$target.parents().eq(3).remove();
                             alert('Please select a  End date');
                        }
                         else if(!_.isEmpty(data_1['date_end'])){
                            ks_self.$target.parents().eq(3).remove();
                            alert('Please select a  Start date');
                        }
                        else{
                            ks_self.$target.parents().eq(3).remove();
                            alert('Please select a  Start and End date');
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