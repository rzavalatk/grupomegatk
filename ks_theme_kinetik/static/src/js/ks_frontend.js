odoo.define('ks_theme_kinetik.ks_frontend', function (require) {
    'use strict';

    var Class = require('web.Class');
    var mixins = require('web.mixins');
    var LazyImageLoader = Class.extend(mixins.EventDispatcherMixin, {
        plugin: null,
        all_finished: null,
        init: function (selector) {
            mixins.EventDispatcherMixin.init.call(this);
            this.all_finished = $.Deferred();
            this.plugin = $(selector).data('loaded', false).lazy(
                this._getPluginConfiguration()
            );
        },
        _getPluginConfiguration: function () {
            return {
                afterLoad: this._afterLoad.bind(this),
                beforeLoad: this._beforeLoad.bind(this),
                onError: this._onError.bind(this),
                onFinishedAll: this._onFinishedAll.bind(this),
                chainable: false,
            };
        },
        _beforeLoad: function (el) {
            this.trigger('beforeLoad', el);
        },
        _afterLoad: function (el) {
            this.trigger('afterLoad', el);
        },
        _onError: function (el) {
            this.trigger('onError', el);
        },
        _onFinishedAll: function () {
            this.all_finished.resolve();
            this.trigger('onFinishedAll');
        },
    });
    require('web.dom_ready');
    var lazy_image_loader = new LazyImageLoader(
        '#wrapwrap > main img:not(.lazyload-disable), ' +
        '#wrapwrap > footer img:not(.lazyload-disable)'
    );
    return {
        LazyImageLoader: LazyImageLoader,
        lazy_image_loader: lazy_image_loader,
    };
});
