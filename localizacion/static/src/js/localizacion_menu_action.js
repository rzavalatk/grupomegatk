odoo.define('localizacion.localizacion_menu_action', function (require) {
    "use strict";

    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction');

    var UserCard = AbstractAction.extend({
        template: 'LocalizacionMenu',
  
        events: {
            'change #filter_selection': '_onChangeFilter',
        },

        _onChangeFilter: function (ev) {
            ev.preventDefault();
            console.log(ev.target.value);
            if ("geolocation" in navigator) {
                // El navegador soporta la API de Geolocalización
                navigator.geolocation.getCurrentPosition(
                  (position) => {
                    // Éxito al obtener la ubicación
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;
                    console.log(`Latitud: ${latitude}, Longitud: ${longitude}`);
                  },
                  (error) => {
                    // Error al obtener la ubicación
                    switch (error.code) {
                      case error.PERMISSION_DENIED:
                        console.error("El usuario denegó la solicitud de geolocalización.");
                        break;
                      case error.POSITION_UNAVAILABLE:
                        console.error("La información de ubicación no está disponible.");
                        break;
                      case error.TIMEOUT:
                        console.error("La solicitud de geolocalización ha expirado.");
                        break;
                      default:
                        console.error("Ocurrió un error desconocido.");
                    }
                  }
                );
              } else {
                // El navegador no soporta la API de Geolocalización
                console.error("Geolocalización no es soportada por este navegador.");
              }
        },
    });

    core.action_registry.add('localizacion_tag', UserCard);

    return UserCard;
});