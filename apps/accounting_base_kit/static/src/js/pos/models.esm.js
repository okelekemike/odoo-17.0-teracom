/** @odoo-module */
/*
    Copyright 2023 Dixmit
    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
*/

import {Order, Orderline, Product} from "@point_of_sale/app/store/models";
import {patch} from "@web/core/utils/patch";

patch(Order.prototype, {
    setup() {
        super.setup(...arguments);
        var default_customer = this.pos.config.res_partner_id;
        var default_customer_by_id = this.pos.db.get_partner_by_id(default_customer[0]);
        if(default_customer_by_id){
            this.set_partner(default_customer_by_id);
        } else{
            this.set_partner(null);
        }
    },
});

patch(Product.prototype, {
    getAddProductOptions() {
        this.pos.selectedProduct = this;
        return super.getAddProductOptions(...arguments);
    },
});

patch(Orderline.prototype, {
    editPackLotLines() {
        this.pos.selectedProduct = this.product;
        return super.editPackLotLines(...arguments);
    },
});