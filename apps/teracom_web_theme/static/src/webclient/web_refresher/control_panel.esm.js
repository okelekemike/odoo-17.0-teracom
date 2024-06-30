/** @odoo-module **/

import { ControlPanel } from "@web/search/control_panel/control_panel";
import { Refresher } from "./refresher.esm";
import { patch } from "@web/core/utils/patch";

patch(ControlPanel, {
    components: {...ControlPanel.components, Refresher},
});

patch(ControlPanel.prototype, {
    /**
     * @returns {{searchModel: Object<*>, pagerProps: Object<*>}|null}
     */
    get refresherProps() {
        const {config, searchModel} = this.env;
        const forbiddenSubType = ["base_settings"];
        if (forbiddenSubType.includes(config.viewSubType)) {
            return null;
        }
        return {
            searchModel: searchModel,
            pagerProps: this.pagerProps,
        };
    },
});
