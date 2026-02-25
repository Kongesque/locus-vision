<script lang="ts">
	import PageTitle2 from '$lib/components/page-title-2.svelte';
	import UploadArea from '$lib/components/video-analytics/upload-area.svelte';
	import SearchInput from '$lib/components/video-analytics/search-input.svelte';
	import VideoCard from '$lib/components/video-analytics/video-card.svelte';
	import QueueStatus from '$lib/components/video-analytics/queue-status.svelte';
	import { onMount, onDestroy } from 'svelte';

	let { data } = $props();
	let history = $state<any[]>(data.history || []);
	let searchQuery = $state('');
	let refreshTimer: ReturnType<typeof setInterval>;

	let filteredHistory = $derived(
		history.filter((item: any) =>
			(item.filename || item.id).toLowerCase().includes(searchQuery.toLowerCase())
		)
	);

	async function refreshHistory() {
		try {
			const res = await fetch('http://127.0.0.1:8000/api/video/history');
			if (res.ok) {
				history = await res.json();
			}
		} catch {
			// silent
		}
	}

	onMount(() => {
		// Auto-refresh history every 5s to pick up completed tasks
		refreshTimer = setInterval(refreshHistory, 5000);
	});

	onDestroy(() => {
		if (refreshTimer) clearInterval(refreshTimer);
	});

	function handleDownload() {
		console.log('Download');
	}

	function handleDelete() {
		console.log('Delete');
	}
</script>

<svelte:head>
	<title>Video Analytics · Locus</title>
</svelte:head>

<div class="flex flex-1 flex-col gap-4 p-4">
	<PageTitle2 />
	<UploadArea />
	<QueueStatus />

	<div class="mt-4 flex flex-col gap-4">
		<SearchInput bind:value={searchQuery} />

		{#if filteredHistory.length > 0}
			<div class="grid grid-cols-1 gap-4 md:grid-cols-4">
				{#each filteredHistory as item (item.id)}
					<VideoCard
						taskId={item.id}
						name={item.filename}
						duration={item.duration || '--:--'}
						createdAt={new Date(item.created_at).toLocaleString()}
						format={item.format || 'mp4'}
						status={item.status}
						progress={item.progress || 0}
						thumbnail={`http://127.0.0.1:8000/api/video/${item.id}/thumbnail`}
						onDownload={handleDownload}
						onDelete={handleDelete}
					/>
				{/each}
			</div>
		{:else}
			<div class="flex h-24 items-center justify-center">
				<span class="text-muted-foreground">No results found.</span>
			</div>
		{/if}
	</div>
</div>
