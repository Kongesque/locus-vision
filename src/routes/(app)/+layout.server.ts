import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ cookies, locals }) => {
    const sidebarState = cookies.get('sidebar:state');
    return {
        sidebarOpen: sidebarState ? sidebarState === 'true' : true,
        user: locals.user
    };
};
