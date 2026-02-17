<script lang="ts">
	import historyData from '../../../../data/video_history.json';
	import PageTitle2 from '$lib/components/page-title-2.svelte';
	import UploadArea from '$lib/components/video-analytics/upload-area.svelte';
	import SearchInput from '$lib/components/video-analytics/search-input.svelte';
	import VideoCard from '$lib/components/video-analytics/video-card.svelte';

	let searchQuery = $state('');
	let loading = $state(false);

	let history = historyData;

	let filteredHistory = $derived(
		history.filter((item) => item.name.toLowerCase().includes(searchQuery.toLowerCase()))
	);

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

	<div class="mt-4 flex flex-col gap-4">
		<SearchInput bind:value={searchQuery} />

		{#if loading}
			<div class="flex justify-center p-8 text-muted-foreground">Loading video tasks...</div>
		{:else if filteredHistory.length > 0}
			<div class="grid grid-cols-1 gap-4 md:grid-cols-4">
				{#each filteredHistory as item (item.id)}
					<VideoCard
						taskId={item.id}
						name={item.name}
						duration={item.duration}
						createdAt={item.createdAt}
						format={item.format}
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
