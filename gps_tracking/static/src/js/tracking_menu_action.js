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
                /^\d{6}$/.test(l) ? l : alert("El ID del dispositivo no es válido");
                return;
            } else {
                alert("Ingrese el ID del dispositivo");
                return;
            }
            alert(l);
            console.log(l);
        },

        start: function () {
            
            return this._super.apply(this, arguments);
        },


    });

    core.action_registry.add('gps_tracking_tag', CustomCardMenu);  // Este es el tag que se llama en el XML
    return CustomCardMenu;
});
