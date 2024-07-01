/** @odoo-module */

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";

export class PutOnHoldButton extends Component {
    static template = "point_of_sale.PutOnHoldButton";

    setup() {
        this.pos = usePos();
        this.ui = useState(useService("ui"));
    }
    async onClick() {
        const order = this.pos.get_order();
        const lines = order.get_orderlines();
        if (lines.length > 0) {
            this.pos.add_new_order();
        }
        this.pos.showScreen("ProductScreen");
    }
}
