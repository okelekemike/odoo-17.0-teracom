/** @odoo-module **/
import { Dropdown } from '@web/core/dropdown/dropdown';
import { DropdownItem } from '@web/core/dropdown/dropdown_item';
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component } from '@odoo/owl';

/* Export new class MailButton by extending Component */
export class MailButton extends Component {
    setup() {
        this.user = useService("user");
    }
    /* On clicking mail icon */
    async onclick_mail_icon() {
        this.env.services['action'].doAction({
            name: "Compose Mail",
            type: "ir.actions.act_window",
            res_model: 'mail.compose.message',
            binding_model_id: 'mail.model_mail_compose_message',
            views: [[false, "form"]],
            view_mode: "form",
            target: "new",
            context: {
                ...this.user.context,
                default_composition_mode: 'comment',
                default_parent_id: this.user.userId,
            },
        });
    }
}
MailButton.template = 'accounting_base_kit.mail_icon';
MailButton.components = {Dropdown, DropdownItem};
export const mailbutton = {
    Component: MailButton,
};
registry.category('systray').add('MailButton', mailbutton);
