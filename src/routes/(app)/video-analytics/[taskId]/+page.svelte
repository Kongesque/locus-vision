<script lang="ts">
	import { page } from '$app/stores';
	import historyData from '../../../../../data/video_history.json';
	import { AspectRatio } from '$lib/components/ui/aspect-ratio/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { ChevronLeft } from '@lucide/svelte';

	let taskId = $derived($page.params.taskId);
	let task = $derived(historyData.find((t) => t.id === taskId));
</script>

<svelte:head>
	<title>{task ? task.name : 'Task Not Found'} · Locus</title>
</svelte:head>

<div class="flex flex-1 flex-col gap-4 p-4">
	<div class="flex items-center gap-4">
		<Button variant="ghost" size="icon" href="/video-analytics">
			<ChevronLeft class="h-4 w-4" />
		</Button>
		<h1 class="text-2xl font-bold tracking-tight">
			{task ? task.name : 'Task Not Found'}
		</h1>
	</div>

	{#if task}
		<div class="flex flex-1 flex-col gap-4 lg:flex-row">
			<div class="flex w-full flex-col gap-4 lg:w-3/4">
				<!-- Video Player -->
				<div class="relative overflow-hidden rounded-lg border bg-black shadow-sm">
					<AspectRatio ratio={16 / 9} class="max-h-[70vh]">
						<!-- TODO: Add actual video source -->
						<!-- svelte-ignore a11y_media_has_caption -->
						<video src="" class="h-full w-full object-contain" controls loop></video>
					</AspectRatio>
				</div>
			</div>

			<!-- Sidebar / Details -->
			<div class="flex w-full flex-col gap-4 lg:w-1/4">
				<div class="rounded-lg border p-4">
					<h3 class="mb-4 font-semibold">Details</h3>
					<div class="flex flex-col gap-2 text-sm text-muted-foreground">
						<div class="flex justify-between">
							<span>Duration</span>
							<span class="font-medium text-foreground">{task.duration}</span>
						</div>
						<div class="flex justify-between">
							<span>Created</span>
							<span class="font-medium text-foreground">{task.createdAt}</span>
						</div>
						<div class="flex justify-between">
							<span>Format</span>
							<span class="font-medium text-foreground">{task.format}</span>
						</div>
					</div>
				</div>
			</div>
		</div>
	{:else}
		<div class="flex flex-1 items-center justify-center">
			<span class="text-muted-foreground">Task not found</span>
		</div>
	{/if}
</div>
