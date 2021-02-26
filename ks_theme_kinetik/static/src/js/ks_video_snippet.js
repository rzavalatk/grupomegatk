odoo.define('ks_theme_kinetik.attach', function(require) {

var session = require('web.session');
var ajax = require('web.ajax');
var core = require('web.core');
var animation = require('website.content.snippets.animation');
var website = require('website.utils');
var _t = core._t;
var Qweb = core.qweb;

 animation.registry.ks_video_snippet = animation.Class.extend({
       selector: ".ks_video_static",
       widget: null,
       template: 'ks_video_data',
       xmlDependencies: ['/ks_theme_kinetik/static/src/xml/ks_attach.xml'],
        ks_handlevideoRecords:function(data,msg_data,$target){
          var $inner_temp = $(Qweb.render('ks_video_data', {
                 "attachment": data,
                 "msg_data" : msg_data,
               }));
               if($target){
                   $inner_temp.appendTo($target.empty());
               }

       },
       start: function (attachment_id,data_1,ks_self_recived) {
            var self = this;
            var data_msg = [];
             self._super();
             this.$el = self.$el;
             if (self.$el){
               data_msg ={
                    'video_message':this.$target.next().text(),
                    'button_message':this.$target.next().next().text(),
                    'button_url'    :this.$target.next().next().attr("href")

               }
             }
             if(ks_self_recived !== undefined){
                this.$target = ks_self_recived.$target;
                this.$el = ks_self_recived.$el;
                self.$target.attr('data-id', attachment_id);
                this.$target.next().text(data_1['video_message'])
                this.$target.next().next().text(data_1['button_message'])
                this.$target.next().next().attr("href", data_1['button_url'])
                data_msg = data_1
            }
            var id = self.$target.attr('data-id');
            if (!parseInt(id)) {
                return;
            }
            if(!data_msg){
                return;
            }

            ajax.post('/product_video/data/read',{'id':id}).then(function(attachment) {
                        this.ks_handlevideoRecords(attachment,data_msg,this.$target);
                        }.bind(this))
        },
    });
})