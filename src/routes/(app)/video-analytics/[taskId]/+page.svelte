<script lang="ts">
	import { page } from '$app/stores';
	import { AspectRatio } from '$lib/components/ui/aspect-ratio/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { ChevronLeft, Loader2 } from '@lucide/svelte';
	import { onMount, onDestroy } from 'svelte';

	let { data } = $props();

	let taskId = $derived(data.taskId);
	let task = $derived(data.task);

	let videoSrc = $state<string | null>(null);
	let status = $state<'loading' | 'processing' | 'ready' | 'error'>('loading');
	let pollInterval: NodeJS.Timeout;

	// Initialize state based on loaded data
	$effect(() => {
		if (task) {
			if (task.status === 'completed') {
				status = 'ready';
				videoSrc = `http://localhost:8000/api/video/${taskId}/result`;
			} else if (task.status === 'failed') {
				status = 'error';
			} else {
				status = 'processing';
			}
		}
	});

	async function checkStatus() {
		// If already ready, no need to check, unless we want to handle re-checks?
		if (status === 'ready') return;

		try {
			const res = await fetch(`http://localhost:8000/api/video/${taskId}/result`);

			if (res.status === 200) {
				// Video is ready
				videoSrc = `http://localhost:8000/api/video/${taskId}/result`;
				status = 'ready';
				stopPolling();
			} else if (res.status === 202) {
				// Still processing
				status = 'processing';
			} else {
				// 404 or other
				// If we know it failed from metadata, we can show error.
				// Or if it's 404 but we expect it to be processing, maybe it takes time to appear?
				// For now, if 404, valid task ID -> processing or queued (unless very old).
				// But `result` endpoint returns 202 if pending/processing/not found but valid?
				// Actually my backend returns 202 if pending. 404 if weird?
				// Let's assume 202.
				if (status !== 'processing') status = 'loading';
			}
		} catch (e) {
			console.error('Error checking status', e);
			// Don't immediately set error on network blip
		}
	}

	function startPolling() {
		if (status === 'ready' || status === 'error') return;
		checkStatus(); // Initial check
		pollInterval = setInterval(checkStatus, 2000);
	}

	function stopPolling() {
		if (pollInterval) clearInterval(pollInterval);
	}

	onMount(() => {
		startPolling();
	});

	onDestroy(() => {
		stopPolling();
	});
</script>

<svelte:head>
	<title>{task ? task.filename : 'Task Result'} · Locus</title>
</svelte:head>

<div class="flex flex-1 flex-col gap-4 p-4">
	<div class="flex items-center gap-4">
		<Button variant="ghost" size="icon" href="/video-analytics">
			<ChevronLeft class="h-4 w-4" />
		</Button>
		<h1 class="text-2xl font-bold tracking-tight">
			{task ? task.filename : `Task ${taskId.slice(0, 8)}`}
		</h1>
		{#if status === 'processing'}
			<div class="flex items-center gap-2 text-sm text-muted-foreground">
				<Loader2 class="h-4 w-4 animate-spin" />
				Processing...
			</div>
		{/if}
	</div>

	<div class="flex flex-1 flex-col gap-4 lg:flex-row">
		<div class="flex w-full flex-col gap-4 lg:w-3/4">
			<!-- Video Player -->
			<div class="group relative overflow-hidden rounded-lg border bg-black shadow-sm">
				<AspectRatio ratio={16 / 9} class="flex max-h-[70vh] items-center justify-center">
					{#if status === 'ready' && videoSrc}
						<!-- svelte-ignore a11y_media_has_caption -->
						<video src={videoSrc} class="h-full w-full object-contain" controls autoplay loop
						></video>
					{:else if status === 'processing' || status === 'loading'}
						<div class="flex flex-col items-center gap-4 text-muted-foreground">
							<Loader2 class="h-8 w-8 animate-spin" />
							<p>Processing video task...</p>
							<p class="text-xs opacity-70">
								This typically takes 10-30 seconds depending on video length.
							</p>
						</div>
					{:else if status === 'error'}
						<div class="flex flex-col items-center gap-2 text-destructive">
							<p>Failed to load video result.</p>
						</div>
					{/if}
				</AspectRatio>
			</div>
		</div>

		<!-- Sidebar / Details -->
		<div class="flex w-full flex-col gap-4 lg:w-1/4">
			<div class="rounded-lg border p-4">
				<h3 class="mb-4 font-semibold">Details</h3>
				<div class="flex flex-col gap-2 text-sm text-muted-foreground">
					{#if task}
						<div class="flex justify-between">
							<span>Duration</span>
							<span class="font-medium text-foreground">{task.duration || '--:--'}</span>
						</div>
						<div class="flex justify-between">
							<span>Created</span>
							<span class="font-medium text-foreground"
								>{new Date(task.created_at).toLocaleString()}</span
							>
						</div>
						<div class="flex justify-between">
							<span>Format</span>
							<span class="font-medium text-foreground">{task.format || 'mp4'}</span>
						</div>
						<div class="flex justify-between">
							<span>Model</span>
							<span class="font-medium text-foreground">{task.model_name || 'N/A'}</span>
						</div>
					{:else}
						<div class="flex justify-between">
							<span>Task ID</span>
							<span class="font-mono text-xs text-foreground">{taskId}</span>
						</div>
						<div class="flex justify-between">
							<span>Status</span>
							<span class="font-medium text-foreground capitalize">{status}</span>
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>
</div>
