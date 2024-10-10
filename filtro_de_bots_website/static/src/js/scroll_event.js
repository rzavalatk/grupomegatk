odoo.define('lt_website_enhancement.scroll_page', function (require) {
'use strict';
    var publicWidget = require('web.public.widget');
    publicWidget.registry.Scroll = publicWidget.Widget.extend({
        selector: '#wrapwrap',
        start: function () {
            var self = this;
            var lastScrollTop = 0;
            var lastScrollLeft = 0;
            self._rpc({
                route: '/website/update_visitor_last_connection',
                params: {
                },
            });
            this._onScroll = function (ev) {
                if(ev.target){
                    var currentScrollTop = ev.target.scrollTop;
                    var currentScrollLeft = ev.target.scrollLeft;
                    var top_difference = Math.abs(currentScrollTop - lastScrollTop);
                    var left_difference = Math.abs(currentScrollLeft - lastScrollLeft);
                    if(top_difference >= 10 || left_difference >= 10){
                        self._rpc({
                            route: '/website/update_visitor_last_connection',
                            params: {
                            },
                        });
                        lastScrollTop = currentScrollTop
                        lastScrollLeft = currentScrollLeft
                    }
                }
            };
            window.addEventListener('scroll', this._onScroll, true);
            return this._super.apply(this, arguments);
        },
    });
    return publicWidget.registry.Scroll;
});
