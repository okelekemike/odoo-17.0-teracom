/** @odoo-module **/

import { useEffect } from "@odoo/owl";
import { session } from "@web/session";
import { url } from "@web/core/utils/urls";
import { useBus, useService } from "@web/core/utils/hooks";

import { Dropdown } from "@web/core/dropdown/dropdown";

export class AppsMenu extends Dropdown {
    setup() {
    	super.setup();
    	this.commandPaletteOpen = false;
        this.commandService = useService("command");
    	this.companyService = useService('company');
    	if (this.companyService.currentCompany.has_background_image) {
            this.backgroundImageUrl = url('/web/image', {
                model: 'res.company',
                field: 'background_image',
                id: this.companyService.currentCompany.id,
            });
    	} else {
    		this.backgroundImageUrl = '/teracom_web_theme/static/src/img/background-light.svg';
    	}
        useEffect(
            (open) => {
            	if (open) {
            		const openMainPalette = (ev) => {
            	    	if (!this.commandServiceOpen && ev.key.length === 1) {
	            	        this.commandService.openMainPalette(
            	        		{ searchValue: `/${ev.key}` }, 
            	        		() => { this.commandPaletteOpen = false; }
            	        	);
	            	    	this.commandPaletteOpen = true;
            	    	}
            		}
	            	window.addEventListener("keydown", openMainPalette);
	                return () => {
	                	window.removeEventListener("keydown", openMainPalette);
	                	this.commandPaletteOpen = false;
	                }
            	}
            },
            () => [this.state.open]
        );
    	useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", this.close);
		window.addEventListener("mousemove", () => {
			if ($(".o_navbar_apps_menu").hasClass('show')) {
				$("#app-menu-io").removeClass("fa-th").addClass("fa-chevron-left");
			} else {
				if (!$("#app-menu-icon").hasClass("o_hidden")) {
					$("#app-menu-io").removeClass("fa-chevron-left").addClass("fa-th");
				}
			}
			if ($(".o_action_manager").is(':visible')) {
				$(".o_navbar_apps_menu ").on("mouseover", (ev) => {
					$("#app-menu-icon").addClass("o_hidden");
					$("#app-menu-io").removeClass("o_hidden");
				}).on("mouseout", (ev) => {
					$("#app-menu-icon").removeClass("o_hidden");
					$("#app-menu-io").addClass("o_hidden");
				})
				$(".o_menu_brand ").on("mouseover", (ev) => {
					$("#app-menu-icon").addClass("o_hidden");
					$("#app-menu-io").removeClass("o_hidden");
				}).on("mouseout", (ev) => {
					$("#app-menu-icon").removeClass("o_hidden");
					$("#app-menu-io").addClass("o_hidden");
				})
			}
			$('.o_action_manager').on("mouseover", (ev) => {
				$("#app-menu-io").addClass("o_hidden");
				$("#app-menu-icon").removeClass("o_hidden");
			})
		})
    }
}

Object.assign(AppsMenu, {
    template: 'teracom_web_theme.AppsMenu',
});
