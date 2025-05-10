/** @odoo-module **/

import { registry } from "@web/core/registry";
import { AbstractAction } from "@web/webclient/actions/abstract_action";
import { loadJS } from "@web/core/assets";
import { patch } from "@web/core/utils/patch";

export class TrackingMenuAction extends AbstractAction {
    setup() {
        super.setup();
        console.log("funciona");
    }
}

registry.category("actions").add("gps_tracking_tag", TrackingMenuAction);
