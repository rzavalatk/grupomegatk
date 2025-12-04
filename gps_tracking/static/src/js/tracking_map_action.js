odoo.define('gps_tracking.tracking_map_action', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const CustomMapMenu = AbstractAction.extend({
        template: 'TrackingMap',
        map: null,
        currentPolyline: null,
        currentRoute: null,

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
            var self =  this;

            if (!trip_id) {
                $('#msg-error').text("Ingrese el codigo del viaje");
                return;
            } else {
                console.log(trip_id);
                
                await self._rpc({
                    model: 'gps.device.trip',
                    method: 'check_code',
                    args: [trip_id],
                }).then(async function (result) {
                    if(result) {
                        if(!/VMT[0-9]{4}/.test(trip_id)) {
                            $('#msg-error').text("El codigo del viaje no es válido");
                            return;
                        } else {
                            $('#msg-error').text("");
                            $('.card-btn').prop('disabled', true).text('Cargando ruta...'); // Asumo que el botón tiene la clase card-btn
                            
                            await self._rpc({
                                model: 'gps.device.trip',
                                method: 'get_locations',
                                args: [trip_id],
                            }).then(function (result) {
                                        // var coords = [
                                        //     [14.09951451320761, -87.18943822450085],
                                        //     [14.0997549384625, -87.18942435633966],
                                        //     [14.099918023980653, -87.1890291137456],
                                        //     [14.099978550535049, -87.18834437328661],
                                        //     [14.100067659044235, -87.18840678001199],
                                        //     [14.100039077073378, -87.18909672103142],
                                        //     [14.100020582855032, -87.18955437035085],
                                        //     [14.100086153258752, -87.18999295100598],

                                        // ];
                                var coords = result;
                                   
                                self._showRoute(coords);
                                self._loadInfo(trip_id);
                                $('.card-btn').prop('disabled', false).text('Mostrar Ruta');
                                console.log(result);
                                
                            }).catch(function (error) {
                                console.error(error);
                                $("#msg-error").text("Error al cargar el viaje");
                            });
                        }
                    } else {
                        $('#msg-error').text("El codigo del viaje no existe");
                        return;
                    }
                })
            }
        },

        _showRoute: function (coords) {
            if(coords && coords.length >= 2) {
                this._clearPolyline();

                const waypoints = coords.map(coord => L.latLng(coord[0], coord[1]));

                // Dibujar la ruta con una polilínea
                this.currentRoute = L.Routing.control({
                    waypoints: waypoints,
                    show: false,
                    routeWhileDragging: false, // No permitir arrastrar los puntos de la ruta
                    showAlternatives: false,  // No mostrar rutas alternativas
                    addWaypoints: false,      // No permitir añadir waypoints interactivos
                    draggableWaypoints: false, // No permitir arrastrar los waypoints existentes
                    fitSelectedRoutes: true,
                    lineOptions: {
                        styles: [{
                            color: '#0099ff',
                            weight: 5,
                            opacity: 1,
                            smoothFactor: 1,
                            className: 'my-route-line'
                        }]
                    }
                }).addTo(this.map);
                console.log("aqui");
            }  else {
                this._clearPolyline(); // Limpiar si no hay suficientes coordenadas
                this.map.setView([14.0989839, -87.1899599], 6); // Volver a vista inicial
                alert("No se encontraron suficientes coordenadas para trazar la ruta (mínimo 2 puntos).");
            }
        },

        _loadInfo: function (id_trip) {
            var self = this;
            self._rpc({
                model: 'gps.device.trip',
                method: 'get_info',
                args: [id_trip],
            }).then(function (result) {
                console.log(result);
                self.$el.find("#trip-device").text(result.id_device);
                self.$el.find("#trip-date").text(result.start_date);
                self.$el.find("#trip-employee").text(result.id_employee);
                self.$el.find("#trip-time").text(result.used_time);
            }).catch(function (error) {
                console.error(error);
            })
        },

        _clearPolyline: function () {
            if (this.currentRoute) {
                this.map.removeControl(this.currentRoute);
                this.routingControl = null;
                console.log("Control de enrutamiento de Leaflet Routing Machine eliminado.");
            }
            if (this.currentPolyline) { // Por si acaso hubiera una polilínea manual
                this.map.removeLayer(this.currentPolyline);
                this.currentPolyline = null;
                console.log("Polilínea manual eliminada del mapa.");
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