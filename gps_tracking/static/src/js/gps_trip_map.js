/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted } from "@odoo/owl";

class TripMapComponent extends Component {
    setup() {
        console.log("Leaflet JS cargado");
        onMounted(() => this.renderMap());
    }

    renderMap() {
        console.log("Leaflet JS cargado");
        
        const el = this.el.querySelector('.leaflet-trip-map');
        if (!el || typeof L === 'undefined') return;

        const map = L.map(el).setView([0, 0], 2);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        // Aquí puedes añadir marcadores desde tu modelo
        const coordinates = this.props.record.data.coordinates || [];
        coordinates.forEach(coord => {
            L.marker([coord.lat, coord.lng]).addTo(map);
        });

        if (coordinates.length > 0) {
            map.setView([coordinates[0].lat, coordinates[0].lng], 13);
        }
    }
}

TripMapComponent.template = "gps_tracking.TripMapComponent";

registry.category("view_widgets").add("leaflet_trip_map", TripMapComponent);
