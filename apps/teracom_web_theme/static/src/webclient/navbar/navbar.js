/** @odoo-module */

import { patch } from '@web/core/utils/patch';

import { NavBar } from '@web/webclient/navbar/navbar';
import { AppsMenu } from "@teracom_web_theme/webclient/appsmenu/appsmenu";
import { AppsBar } from '@teracom_web_theme/webclient/appsbar/appsbar';

patch(NavBar.prototype, {
    getAppsMenuItems() {
        const currentApp = this.menuService.getCurrentApp();
        const menuItems = this.menuService.getApps().map((menu) => {
            const appsMenuItem = {
                id: menu.id,
                name: menu.name,
                xmlid: menu.xmlid,
                appID: menu.appID,
                actionID: menu.actionID,
                href: this.getMenuItemHref(menu),
                action: () => this.menuService.selectMenu(menu),
                active: currentApp && menu.id === currentApp.id,
            };
            if (menu.webIconData) {
                const prefix = (
                    menu.webIconData.startsWith('P') ?
                        'data:image/svg+xml;base64,' :
                        'data:image/png;base64,'
                );
                appsMenuItem.webIconData = (
                    menu.webIconData.startsWith('data:image') ?
                        menu.webIconData :
                        prefix + menu.webIconData.replace(/\s/g, '')
                );
            }
            return appsMenuItem;
        });
        return menuItems;
    },
    getCurrentMenuWebIconData() {
        const currentAppIcon = this.menuService.getCurrentApp();
        if (currentAppIcon && currentAppIcon.webIconData) {
            const prefix = (
                currentAppIcon.webIconData.startsWith('P') ?
                    'data:image/svg+xml;base64,' :
                    'data:image/png;base64,'
            );
            return (
                currentAppIcon.webIconData.startsWith('data:image') ?
                    currentAppIcon.webIconData :
                    prefix + currentAppIcon.webIconData.replace(/\s/g, '')
            );
        }
        return null;
    }
});

patch(NavBar, {
    components: {
        ...NavBar.components,
        AppsMenu,
        AppsBar,
    },
});
