odoo.define('localizacion.localizacion_menu_action', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.public.widget');

    var UserCard = Widget.extend({
        template: 'LocalizacionMenu',
        
        events: {
            'click .btn-primary': '_onClickButton',
        },

        _onClickButton: function (ev) {
            ev.preventDefault();
            alert('¡Hola! Este es un mensaje de ejemplo.');
        },
    });

    core.action_registry.add('user_card', UserCard);

    return UserCard;
});