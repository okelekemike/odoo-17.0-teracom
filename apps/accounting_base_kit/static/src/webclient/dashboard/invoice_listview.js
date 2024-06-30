/** @odoo-module **/
import {
    registry
} from "@web/core/registry";
import {
    listView
} from "@web/views/list/list_view";
import {
    ListRenderer
} from "@web/views/list/list_renderer";
import {
    AccountDashboard
} from '@accounting_base_kit/webclient/dashboard/invoice_dashboard';

export class AccountDashBoardRenderer extends ListRenderer {};

AccountDashBoardRenderer.template = 'accounting_base_kit.AccountListView';
AccountDashBoardRenderer.components = Object.assign({}, ListRenderer.components, {
    AccountDashboard
})
export const AccountDashboardListView = {
    ...listView,
    Renderer: AccountDashBoardRenderer,
};
registry.category("views").add("account_dashboard_list", AccountDashboardListView);
