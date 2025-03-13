odoo.define('localizacion.LeafletMap', function (require) {
  "use strict";

  const { Widget } = require('web.Widget');

  const LeafletMap = Widget.extend({
      template: 'LeafletMap',
      start: function () {
          // Inicializar el mapa
          const map = L.map('map').setView([40.4168, -3.7038], 6); // Centro en España

          // Añadir capa de OpenStreetMap
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
              attribution: '© OpenStreetMap contributors'
          }).addTo(map);

          // Escuchar clics en el mapa
          map.on('click', function (e) {
              const { lat, lng } = e.latlng;
              document.getElementById('coordinates').innerText = `Latitud: ${lat.toFixed(4)}, Longitud: ${lng.toFixed(4)}`;
          });
      },
  });

  return LeafletMap;
});