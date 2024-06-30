/** @odoo-module **/
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { SaleDashBoard } from '@accounting_base_kit/webclient/dashboard/sale_dashboard';

/**
 * Sale Dashboard Renderer class for list view, extending the base ListRenderer.
 * @extends ListRenderer
 */
export class SaleDashBoardRenderer extends ListRenderer {};

// Template for the SaleDashBoardRenderer component
SaleDashBoardRenderer.template = 'accounting_base_kit.SaleListView';

// Components used by SaleDashBoardRenderer
SaleDashBoardRenderer.components = Object.assign({}, ListRenderer.components, { SaleDashBoard });

/**
 * Sale Dashboard List View configuration.
 * @type {Object}
 */
export const SaleDashBoardListView = {
    ...listView,
    // Use the custom SaleDashBoardRenderer as the renderer for the list view
    Renderer: SaleDashBoardRenderer,
};

// Register the Sale Dashboard List View in the "views" category of the registry
registry.category("views").add("sale_dashboard_list", SaleDashBoardListView);
