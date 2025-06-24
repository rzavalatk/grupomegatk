odoo.define('pos_slide_to_delete.Orderline', function(require) {
    'use strict';

    const { useListener } = require("@web/core/utils/hooks");
    const Orderline = require('point_of_sale.Orderline');
    const Registries = require('point_of_sale.Registries');

    const PosSwipeToDelOrderline = Orderline =>
        class extends Orderline {
            get addedClasses() {
                return Object.assign({'deleting': this.deleting}, super.addedClasses);
            }
            checkDirection(e) {
              var touch = e.changedTouches.item(0)
              if ((this.touchstartX - this.touchendX) > Math.max(touch.radiusX * 2,20)) {
              this.trigger('select-line', { orderline: this.props.line });
                var order = this.env.pos.get_order();
                if (order.get_selected_orderline()) {
                    this.deleting =  true
                    setTimeout(() => {
                      order.remove_orderline(order.get_selected_orderline());
                      this.deleting =  false
                    }, 500);
                }
              }
            }
            setup(){
                super.setup();
                this.touchstartX = 0
                this.touchendX = 0
                this.deleting = false
                useListener('touchstart', e => {
                  this.touchstartX = e.changedTouches.item(0).screenX
                });
                useListener('touchend', e => {
                  this.touchendX = e.changedTouches.item(0).screenX
                  this.checkDirection(e)

                });
            }
        };

    Registries.Component.extend(Orderline, PosSwipeToDelOrderline);

    return Orderline;
});
