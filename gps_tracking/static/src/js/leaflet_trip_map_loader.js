// odoo.define('gps_tracking.LeafletTripMapLoader', function (require) {
//     "use strict";

//     const FormController = require('web.FormController');
//     const core = require('web.core');
//     const LeafletTripMap = require('gps_tracking.LeafletTripMap');

//     const LeafletFormController = FormController.extend({
//         _renderView: function () {
//             const self = this;
//             return this._super.apply(this, arguments).then(function () {
//                 if (self.modelName === 'gps.device.trip') {
//                     const recordId = self.renderer.state.res_id;
//                     if (recordId) {
//                         const $mapContainer = self.$el.find('#trip_map_container');
//                         if ($mapContainer.length && !$mapContainer.hasClass('map-rendered')) {
//                             $mapContainer.addClass('map-rendered'); // evitar doble renderizado
//                             const mapWidget = new LeafletTripMap(self, { trip_id: recordId });
//                             mapWidget.appendTo($mapContainer);
//                         }
//                     }
//                 }
//             });
//         }
//     });

//     core.action_registry.add('gps_tracking_form_controller', LeafletFormController);
// });
