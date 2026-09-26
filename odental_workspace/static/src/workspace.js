/** @odoo-module **/
import { patch } from '@web/core/utils/patch';
import { menuService } from '@web/webclient/menus/menu_service';
import { session } from '@web/session';

// Presentation only: never changes ACLs, record rules, or the underlying menu data.
patch(menuService, {
    dependencies: [...menuService.dependencies, 'company'],
    async start(env, services) {
        const menus = await super.start(env, services);
        const configured = session.odental_workspaces?.[services.company.currentCompany.id];
        if (!configured || !configured.length) {
            return menus;
        }
        const allowed = new Set(configured);
        const visible = (menu) => menu.id === 'root' || allowed.has(menu.appID || menu.id);
        const getApps = menus.getApps.bind(menus);
        const getAll = menus.getAll.bind(menus);
        const getTree = menus.getMenuAsTree.bind(menus);
        menus.getApps = () => getApps().filter(visible);
        menus.getAll = () => getAll().filter(visible);
        menus.getMenuAsTree = (id) => {
            const tree = getTree(id);
            if (id !== 'root') {
                return tree;
            }
            return {
                ...tree,
                children: tree.children.filter((child) => allowed.has(child)),
                childrenTree: tree.childrenTree.filter(visible),
            };
        };
        return menus;
    },
});
