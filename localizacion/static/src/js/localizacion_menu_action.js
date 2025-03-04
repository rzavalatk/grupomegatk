odoo.define('localizacion.user_card', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.widget');

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