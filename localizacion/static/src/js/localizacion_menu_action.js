odoo.define('localizacion.localizacion_menu_action', function (require) {
    "use strict";

    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction');

    var UserCard = AbstractAction.extend({
        template: 'LocalizacionMenu',
  
        events: {
            'click .btn-primary': '_onClickButton',
        },

        _onClickButton: function (ev) {
            ev.preventDefault();
            alert('¡Hola! Este es un mensaje de ejemplo.');
        },
    });

    core.action_registry.add('localizacion_tag', UserCard);

    return UserCard;
});