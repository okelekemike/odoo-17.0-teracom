/**@odoo-module **/

import { Component, useRef } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";

import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { patch } from "@web/core/utils/patch";

export class SetProductListButton extends Component {
  static template = "SetProductListButton";

  setup() {
    super.setup();
    this.pos = usePos();
  }
  get productsList() {
    let list = [];
    list = this.pos.db.get_product_by_category(
        this.pos.selectedCategoryId
    );
    return list.sort(function (a, b) {
      return a.display_name.localeCompare(b.display_name);
    });
  }
  onClick_ProductListScreen() {
    let list = this.productsList;
    const screen = "ProductListScreen";
    this.pos.showScreen("ProductListScreen");
  }
}
ProductScreen.addControlButton({
  component: SetProductListButton,
  condition: function () {
    return this.pos.get_cashier().role === "manager";
  },
});

patch(Navbar.prototype, {
  get productsList() {
    let list = [];
    list = this.pos.db.get_product_by_category(
        this.pos.selectedCategoryId
    );
    return list.sort(function (a, b) {
      return a.display_name.localeCompare(b.display_name);
    });
  },
  onClick_ProductListScreen() {
    let list = this.productsList;
    this.pos.showScreen("ProductListScreen");
  },
});
