import { API_URL } from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url }) => {
	const preselectedCamera = url.searchParams.get('camera') ?? undefined;
    // Let's fetch the available cameras to populate the dropdown
    try {
        const res = await fetch(`${API_URL}/api/cameras`);
        if (res.ok) {
            const cameras = await res.json();
            return { cameras, preselectedCamera };
        }
    } catch (e) {
        console.error('Failed to load cameras for analytics', e);
    }
    return { cameras: [], preselectedCamera };
};
