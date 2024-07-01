/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { parseFloat } from "@web/views/fields/parsers";

export class DiscountButton extends Component {
    static template = "pos_discount.DiscountButton";

    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
    }
    async click() {
        var self = this;
        var discount_type = await self.getDiscountType();
        var discount_icon = "Discount (" + discount_type === 'amount' ? 'Amount' : 'Percentage' + ")";
        var discount_amt = await self.getDiscountAmt();

        const { confirmed, payload } = await this.popup.add(NumberPopup, {
            title: _t(discount_icon),
            startingValue: this.pos.config.discount_pc,
            isInputSelected: true,
        });
        if (confirmed) {
            const val = Math.max(0, Math.min(discount_type === 'amount' ? discount_amt : 100, parseFloat(payload)));
            await self.apply_discount(val, discount_type);
        }
    }

    async apply_discount(pc, d_type) {
        const order = this.pos.get_order();
        const lines = order.get_orderlines();
        const product = this.pos.db.get_product_by_id(this.pos.config.discount_product_id[0]);
        if (product === undefined) {
            await this.popup.add(ErrorPopup, {
                title: _t("No discount product found"),
                body: _t(
                    "The discount product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'."
                ),
            });
            return;
        }

        // Remove existing discounts
        lines
            .filter((line) => line.get_product() === product)
            .forEach((line) => order._unlinkOrderline(line));

        // Add one discount line per tax group
        const linesByTax = order.get_orderlines_grouped_by_tax_ids();
        for (const [tax_ids, lines] of Object.entries(linesByTax)) {
            // Note that tax_ids_array is an Array of tax_ids that apply to these lines
            // That is, the use case of products with more than one tax is supported.
            const tax_ids_array = tax_ids
                .split(",")
                .filter((id) => id !== "")
                .map((id) => Number(id));

            const baseToDiscount = order.calculate_base_amount(
                tax_ids_array,
                lines.filter((ll) => ll.isGlobalDiscountApplicable())
            );

            // We add the price as manually set to avoid recomputation when changing customer.
            const discount = d_type === 'amount' ? -pc : ((-pc / 100.0) * baseToDiscount);
            const d_pc = d_type === 'amount' ? (pc / baseToDiscount * 100) : pc;
            if (discount < 0) {
                order.add_product(product, {
                    price: discount,
                    lst_price: discount,
                    tax_ids: tax_ids_array,
                    merge: false,
                    description:
                        `${d_pc}%, ` +
                        (tax_ids_array.length
                            ? _t(
                                  "Tax: %s",
                                  tax_ids_array
                                      .map((taxId) => this.pos.taxes_by_id[taxId].amount + "%")
                                      .join(", ")
                              )
                            : _t("No tax")),
                    extras: {
                        price_type: "automatic",
                    },
                });
            }
        }
    }

    async getDiscountType() {
        if (this.pos.config.discount_type === "both") {
            const { confirmed } = await this.popup.add(ConfirmPopup, {
                title: _t('Select Discount Type'),
                body: _t(
                    'Please select the type of global discount to be applied'
                ),
                cancelText: _t("Amount"),
                confirmText: _t("Percentage"),
            });
            return confirmed ? 'percentage' : 'amount';
        } else {
            return this.pos.config.discount_type;
        }
    }

    async getDiscountAmt() {
        if (this.pos.config.discount_max_amount > 0) {
            return  this.pos.config.discount_max_amount;
        } else {
            return 1000000;
        }
    }
}

ProductScreen.addControlButton({
    component: DiscountButton,
    condition: function () {
        const { module_pos_discount, discount_product_id } = this.pos.config;
        return module_pos_discount && discount_product_id;
    },
});
