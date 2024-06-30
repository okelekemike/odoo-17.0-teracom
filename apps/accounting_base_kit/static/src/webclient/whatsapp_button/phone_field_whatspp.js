/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { PhoneField, phoneField, formPhoneField } from "@web/views/fields/phone/phone_field";
import { SendWhatsappButton } from './whatsapp_button';

patch(PhoneField, {
    components: {
        ...PhoneField.components,
        SendWhatsappButton
    },
    defaultProps: {
        ...PhoneField.defaultProps,
        enableButton: true,
    },
    props: {
        ...PhoneField.props,
        enableButton: { type: Boolean, optional: true },
    },
});

const patchDescr = () => ({
    extractProps({ options }) {
        const props = super.extractProps(...arguments);
        props.enableButton = options.enable_whatsapp;
        return props;
    },
    supportedOptions: [{
        label: _t("Enable WhatsApp"),
        name: "enable_whatsapp",
        type: "boolean",
        default: true,
    }],
});

patch(phoneField, patchDescr());
patch(formPhoneField, patchDescr());
