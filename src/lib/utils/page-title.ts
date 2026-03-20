export const titleMap: Record<string, string> = {
	'/': 'Dashboard',
	'/livestream': 'Livestream',
	'/video-analytics': 'Video Analytics',
	'/analytics': 'Historical Analytics',
	'/settings': 'Settings',
	'/system': 'System'
};

export function getPageTitle(pathname: string): string {
	// Check exact match first
	if (titleMap[pathname]) {
		return titleMap[pathname];
	}

	// Handle dynamic routes - derive from parent route
	// /livestream/[taskId] → Livestream
	if (pathname.startsWith('/livestream/')) {
		return 'Livestream';
	}

	// /video-analytics/[taskId] → Video Analytics
	if (pathname.startsWith('/video-analytics/')) {
		return 'Video Analytics';
	}

	// /create/[taskId] → Create
	if (pathname.startsWith('/create/')) {
		return 'Create';
	}

	return 'Locus';
}
