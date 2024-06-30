/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { Component, status } from "@odoo/owl";

export class SendWhatsappButton extends Component {
    setup() {
        this.action = useService("action");
        this.user = useService("user");
        this.title = _t("Send WhatsApp Message");
    }
    get phoneHref() {
        return "whatsapp:" + this.props.record.data[this.props.name].replace(/\s+/g, "");
    }
    async onClick() {
        await this.props.record.save();
        this.action.doAction(
            {
                type: "ir.actions.act_window",
                target: "new",
                name: this.title,
                res_model: "whatsapp.send.message",
                views: [[false, "form"]],
                context: {
                    ...this.user.context,
                    default_partner_id: this.props.record.resId,
                    default_mobile: this.props.record.data[this.props.name].replace(/\s+/g, ""),
                    default_image_1920: this.props.record.data.image_1920,
                },
            },
            {
                onClose: () => {
                    if (status(this) === "destroyed") {
                        return;
                    }
                    this.props.record.load();
                },
            }
        );
    }
}
SendWhatsappButton.template = "whatsapp.SendWhatsappButton";
SendWhatsappButton.props = ["*"];
