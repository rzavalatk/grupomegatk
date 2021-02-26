odoo.define('ks_theme_kinetik.deal_of_the_day', function(require) {

var session = require('web.session');
var ajax = require('web.ajax');
var core = require('web.core');
var animation = require('website.content.snippets.animation');
var website = require('website.utils');
var _t = core._t;
var Qweb = core.qweb;

 animation.registry.ks_deal_of_the_day_snippet = animation.Class.extend({
       selector: ".ks_deal_of_the_day_base",
       widget: null,
       template: 'ks_dynamic_offer_snippets',
       xmlDependencies: ['/ks_theme_kinetik/static/src/xml/ks_deal_of_the_day.xml'],
          ks_handlevideoRecords:function(sec,data,$target){
          var $inner_temp = $(Qweb.render('ks_dynamic_offer_snippets', {
                 "seconds": sec,
                 "data_msg":data,
               }));
               if($target){
                    if(sec){
                        $inner_temp.find('.ks_clock').removeClass("d-none");
                        var clock = $inner_temp.find('.ks_clock').FlipClock(sec, {
                                    clockFace: 'DailyCounter',
                                    countdown: true,
                                    });
                    }
                   $inner_temp.appendTo($target.empty());
                   $('.ks_clock').find('.flip-clock-label').remove();
               }

       },
       start: function (data_1,ks_self_recived) {
            var self = this;
            var data_msg = [];
             self._super();
             this.$el = self.$el;
             if (self.$el){
               data_msg ={
                    'date_start'    :this.$target.parents().eq(3).find('.ks_date_start').text(),
                    'button_message':this.$target.parents().eq(3).find('.ks_date_start').next().text(),
                    'button_url'    :this.$target.parents().eq(3).find('.ks_date_start').next().attr("href")
               }
             }
             if(ks_self_recived !== undefined){
                this.$target = ks_self_recived.$target;
                this.$el = ks_self_recived.$el;
                self.$target.attr('data-id', data_1['date_end']);
                this.$target.parents().eq(3).find('.ks_date_start').text(data_1['date_start'])
                this.$target.parents().eq(3).find('.ks_date_start').next().text(data_1['button_message'])
                this.$target.parents().eq(3).find('.ks_date_start').next().attr("href", data_1['button_url'])
                data_msg = data_1
            }
            var date_end = self.$target.attr('data-id');
            data_msg['date_end'] = date_end
            if(!data_msg){
                return;
            }
             ajax.post('/deal_of_day/data/second/create', data_msg).then(function(seconds){
                     if(seconds.seconds){
                        this.$target.parents().eq(3).removeClass('d-none')
                        this.ks_handlevideoRecords(seconds.seconds,data_msg,this.$target);
                     }
                     else{
                        if(data_msg["date_end"].length){
                             this.$target.parents().eq(3).remove();
                             return
                        }
                        else{
                            return;
                        }

                     }}.bind(this))
        },
    });
})