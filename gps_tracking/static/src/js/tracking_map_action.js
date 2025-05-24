odoo.define('gps_tracking.tracking_map_action', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const CustomMapMenu = AbstractAction.extend({
        template: 'TrackingMap',
        map: null,
        currentPolyline: null,

        events: {
            "click .card-btn": "_onClickMostrarRuta", 
        },

        _onClickMostrarRuta: function (e) {
            e.preventDefault();
            var id = $('#id_device').val();
            this._loadCoords(id);
        },

        start: function () {
            console.log("funciona");
            // No necesitamos llamar a _initLeafletMap directamente aquí,
            // ya que lo haremos en on_attach_callback para mayor seguridad.
            return this._super.apply(this, arguments);
        },

        // Este método se llama cuando el widget se inserta en el DOM y está visible.
        on_attach_callback: function () {
            // Asegúrate de que el mapa se inicialice solo una vez.
            if (!this.map) {
                this._initLeafletMap();
            } else {
                // Si el mapa ya existe (e.g., el widget fue temporalmente oculto y ahora se muestra de nuevo),
                // asegúrate de que su tamaño sea invalidado.
                this.map.invalidateSize();
            }
            console.log("on_attach_callback llamado. Mapa debería estar visible y correcto.");
        },

        _initLeafletMap: function () {
            const mapContainer = this.$('#map')[0];
            if (mapContainer) {
                try {
                    this.map = L.map(mapContainer).setView([14.0989839, -87.1899599], 6);

                    // Cargar mapa base de OpenStreetMap
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                    }).addTo(this.map);

                    // Agregar marcador
                    L.marker([14.0989839, -87.1899599]).addTo(this.map)
                    .bindPopup('Ubicación inicial')
                    .openPopup();
                    
                    // Llama a invalidateSize() aquí también, por si acaso.
                    // on_attach_callback ya garantiza la visibilidad, pero no está de más.
                    this.map.invalidateSize();
                    console.log("Mapa Leaflet inicializado y tamaño invalidado.");

                } catch (e) {
                    console.error("Error al inicializar el mapa Leaflet:", e);
                    this.map = null;
                }
            } else {
                console.error("No se pudo encontrar el contenedor del mapa (#map).");
            }
        },

        _loadCoords: async function (trip_id) {
            console.log(`Mostrar ruta ${trip_id}`);

            var self = this;

            self._rpc({
                model: 'gps.device.trip',
                method: 'get_locations',
                args: [trip_id],
            }).then(function (result) {
                self._showRoute(result);
                console.log(result);
            }).catch(function (error) {
                console.error(error);
            });
            // try {
            //     const coordinates = await this._rpc({
            //         model: 'gps.device.location',
            //         method: 'get_locations',
            //         args: [trip_id],
            //     });

            //     console.log("Coordenadas obtenidas:", coordinates);

            //     if(coordinates && coordinates.length > 0) {

            //         this._clearPolyline();
            //         // Dibujar la ruta con una polilínea
            //         this.currentPolyline = L.polyline(coordinates, {
            //             color: '#0099ff',
            //             weight: 5,
            //             opacity: 1,
            //             smoothFactor: 1,
            //             className: 'my-route-line'
            //         }).addTo(this.map);
            //     }
                
            // }


            // // Dibujar la ruta con una polilínea
            

            // for (var i = 0; i < puntosRuta.length; i++) {
            //     L.marker(puntosRuta[i]).addTo(this.map);
            //     L.marker([14.0989839, -87.1899599]).addTo(this.map)
            //     .bindPopup('Ubicación inicial')
            //     .openPopup();
            // }
        },

        _showRoute: function (coords) {
            this._clearPolyline();
            // Dibujar la ruta con una polilínea
            this.currentPolyline = L.polyline(coordinates, {
                color: '#0099ff',
                weight: 5,
                opacity: 1,
                smoothFactor: 1,
                className: 'my-route-line'
            }).addTo(this.map);

            for (var i = 0; i < puntosRuta.length; i++) {
                L.marker(puntosRuta[i]).addTo(this.map);
            }
        },

        _clearPolyline: function () {
            if (this.currentPolyline) {
                this.map.removeLayer(this.currentPolyline);
                this.currentPolyline = null;
                console.log("Polilínea anterior eliminada del mapa.");
            }
        },

        destroy: function () {
            if (this.map) {
                this.map.remove();
                this.map = null;
            }
            this._super.apply(this, arguments);
            console.log("CustomMapMenu destruido y mapa removido.");
        }
    });

    core.action_registry.add('gps_map_tag', CustomMapMenu);
    return CustomMapMenu;
});