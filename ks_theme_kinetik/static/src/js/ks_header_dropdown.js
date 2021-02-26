odoo.define('ks_website.HeaderDropdown', function (require) {
'use strict';

    var ks_dropdown_menu=require('website.content.menu');
    var sAnimations = require('website.content.snippets.animation');

    sAnimations.registry.affixMenu.include({
        start : function(){
            this._super.apply(this, arguments);
            $(".ks_landing_menu.dropdown li").on('mouseenter mouseleave', function (e) {
                if ($('ul', this).length) {
                    var elm = $('ul:first', this);
                    var off = elm.offset();
                    var l = off.left;
                    var r = ($(window).width() - (l + elm.outerWidth()));
                    var w = elm.width();
                    var docH = $(window).height();
                    var docW = $(window).width();

                    if($(".o_rtl").length){
                        var isEntirelyVisible = (r + w <= docW);
                        if (!isEntirelyVisible) {
                            $(this).addClass('ks_edge');
                        } else {
                            $(this).removeClass('ks_edge');
                        }
                    }
                    else{
                        var isEntirelyVisible = (l + w <= docW);
                        if (!isEntirelyVisible) {
                            $(this).addClass('ks_edge');
                        } else {
                            $(this).removeClass('ks_edge');
                        }
                    }
                }
            });
        }
    })
})