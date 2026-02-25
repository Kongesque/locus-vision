import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

const API_BASE = 'http://127.0.0.1:8000';

export interface VideoTask {
    id: string;
    filename: string;
    status: string;
    progress: number;
    created_at: string;
    completed_at: string | null;
    duration: string | null;
    format: string | null;
    model_name: string | null;
    total_count: number | null;
    zone_counts: string | null;
    error_message: string | null;
}

export const load: PageLoad = async ({ fetch }) => {
    try {
        const res = await fetch(`${API_BASE}/api/video/history`);
        if (res.ok) {
            const history: VideoTask[] = await res.json();
            return {
                history
            };
        }
        return {
            history: []
        };
    } catch (e) {
        console.error('Failed to load video history:', e);
        return {
            history: []
        };
    }
};
