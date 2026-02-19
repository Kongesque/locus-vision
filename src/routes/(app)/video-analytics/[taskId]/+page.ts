import type { PageLoad } from './$types';
import type { VideoTask } from '../+page';

const API_BASE = 'http://127.0.0.1:8000';

export const load: PageLoad = async ({ params, fetch }) => {
    const taskId = params.taskId;
    try {
        // We can reuse the history endpoint to find the specific task, 
        // OR ideally we should have a specific endpoint. 
        // For now, let's fetch history and find it, or fallback to just ID if not found/API pending.
        // Actually, the backend doesn't have a specific "get task details" endpoint other than result/thumbnail check.
        // But we DO have the `get_history` list. 
        // Let's use that for metadata for now.
        const res = await fetch(`${API_BASE}/api/video/history`);
        if (res.ok) {
            const history: VideoTask[] = await res.json();
            const task = history.find(t => t.id === taskId);
            return {
                task,
                taskId
            };
        }
        return {
            task: null,
            taskId
        };
    } catch (e) {
        console.error('Failed to load video task:', e);
        return {
            task: null,
            taskId
        };
    }
};
