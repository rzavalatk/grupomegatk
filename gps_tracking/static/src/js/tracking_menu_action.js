odoo.define('gps_tracking.tracking_menu_action', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const CustomCardMenu = AbstractAction.extend({
        template: 'TrackingCardMenu',

        events: {
            "click .btn-success": "_onClickIniciarViaje",
            "click .btn-warning": "_onClickPrueba",
        },

        _onClickIniciarViaje: function () {
            this._startTrip();
        },

        _startTrip: function() {
            var self = this;
            var l = self.$el.find("#id_device").val();
            if(l != '') {
                if (/^\d{6}$/.test(l)) {
                    self.$el.find("#msg-text").text("");
                    self._rcp({
                        
                    })
                } else {
                    self.$el.find("#msg-text").text("El ID del dispositivo no es válido");
                    return;    
                }
            } else if (l == '') {
                alert("Ingrese el ID del dispositivo");
                return;
            }
        },

        start: function () {
            
            return this._super.apply(this, arguments);
        },


    });

    core.action_registry.add('gps_tracking_tag', CustomCardMenu);  // Este es el tag que se llama en el XML
    return CustomCardMenu;
});
