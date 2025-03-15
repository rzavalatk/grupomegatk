odoo.define('gps_localizacion.GpsButton', function (require) {
  "use strict";

  var core = require('web.core');
  var Widget = require('web.Widget');
  var rpc = require('web.rpc');

  var GpsButton = Widget.extend({
      template: 'GpsButton',
      events: {
          'click .toggle-gps': 'onToggleGps',
      },

      init: function (parent, options) {
          this._super.apply(this, arguments);
          this.isTracking = false;
          this.intervalId = null;
      },

      onToggleGps: function () {
          var self = this;
          if (this.isTracking) {
              // Detener el seguimiento
              clearInterval(this.intervalId);
              this.isTracking = false;
              this.$el.find('.toggle-gps').text('Iniciar GPS');
          } else {
              // Iniciar el seguimiento
              this.isTracking = true;
              this.$el.find('.toggle-gps').text('Detener GPS');
              this.intervalId = setInterval(function () {
                  self.getLocation();
              }, 5 * 60 * 1000); // Intervalo de 5 minutos
          }
      },

      getLocation: function () {
          var self = this;
          if (navigator.geolocation) {
              navigator.geolocation.getCurrentPosition(
                  function (position) {
                      var latitude = position.coords.latitude;
                      var longitude = position.coords.longitude;
                      self.saveLocation(latitude, longitude);
                  },
                  function (error) {
                      console.error("Error obteniendo la ubicación: ", error);
                  }
              );
          } else {
              console.error("Geolocalización no soportada en este navegador.");
          }
      },

      saveLocation: function (latitude, longitude) {
          rpc.query({
              route: '/gps/save_location',
              params: {
                  latitude: latitude,
                  longitude: longitude,
              },
          }).then(function (result) {
              console.log("Ubicación guardada:", result);
          });
      },
  });

  core.action_registry.add('gps_button', GpsButton);
  return GpsButton;
});