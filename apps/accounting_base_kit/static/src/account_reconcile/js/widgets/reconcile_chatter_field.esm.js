/** @odoo-module **/

import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {Chatter} from "@mail/core/web/chatter";

const {Component} = owl;

export class AccountReconcileChatterWidget extends Component {}
AccountReconcileChatterWidget.props = {...standardFieldProps};
AccountReconcileChatterWidget.template =
    "accounting_base_kit.AccountReconcileChatterWidget";
AccountReconcileChatterWidget.components = {...Component.components, Chatter};
export const AccountReconcileChatterWidgetField = {
    component: AccountReconcileChatterWidget,
    supportedTypes: [],
};
registry
    .category("fields")
    .add("account_reconcile_oca_chatter", AccountReconcileChatterWidgetField);
