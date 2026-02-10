<script lang="ts">
	import { page } from '$app/state';

	const titleMap: Record<string, string> = {
		'/': 'Home',
		'/livestream': 'Live Stream',
		'/video-analytics': 'Video Analytics',
		'/settings': 'Settings'
	};

	let title = $derived(titleMap[page.url.pathname] || 'Locus');
</script>

<div class="flex items-center gap-2 px-4">
	<h1 class="text-xl font-bold tracking-tight">{title}</h1>
</div>
