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
	<div class="mb-2 flex items-center justify-between">
		<div class="flex items-center gap-4">
			<Button variant="ghost" size="icon" href="/video-analytics">
				<ChevronLeft class="h-4 w-4" />
			</Button>
			<h1 class="text-2xl font-bold tracking-tight">
				{task ? task.filename : `Task ${taskId.slice(0, 8)}`}
			</h1>
		</div>
		<div class="flex items-center gap-2">
			<span class="relative flex h-3 w-3">
				{#if status === 'processing' || status === 'loading'}
					<span
						class="absolute inline-flex h-full w-full animate-ping rounded-full bg-yellow-400 opacity-75"
					></span>
					<span class="relative inline-flex h-3 w-3 rounded-full bg-yellow-500"></span>
				{:else if status === 'ready'}
					<span
						class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"
					></span>
					<span class="relative inline-flex h-3 w-3 rounded-full bg-green-500"></span>
				{:else}
					<span class="relative inline-flex h-3 w-3 rounded-full bg-red-500"></span>
				{/if}
			</span>
			<span class="text-sm font-medium text-muted-foreground capitalize">
				{status === 'loading' ? 'connecting' : status}
			</span>
		</div>
	</div>

	{#if status === 'error'}
		<div class="rounded-md border border-red-500/20 bg-red-500/10 p-4 text-red-500">
			Failed to load video result.
		</div>
	{/if}

	<div class="flex flex-1 flex-row gap-4">
		<div class="mx-auto flex w-full max-w-5xl flex-col gap-4">
			<div class="relative overflow-hidden rounded-lg border bg-black shadow-lg">
				<AspectRatio ratio={16 / 9} class="group relative max-h-[80vh]">
					{#if status === 'ready' && videoSrc}
						<!-- svelte-ignore a11y_media_has_caption -->
						<video
							src={videoSrc}
							class="h-full w-full object-contain"
							controls
							autoplay
							loop
							playsinline
							crossorigin="anonymous"
						></video>
					{:else if status === 'processing' || status === 'loading'}
						<div
							class="flex h-full flex-col items-center justify-center gap-4 text-muted-foreground"
						>
							<Loader2 class="h-8 w-8 animate-spin" />
							<p>Processing video task...</p>
							<p class="text-xs opacity-70">
								This typically takes 10-30 seconds depending on video length.
							</p>
						</div>
					{/if}
				</AspectRatio>
			</div>

			<div class="grid grid-cols-3 gap-4">
				<div class="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
					<div class="text-sm font-semibold text-muted-foreground">Detection Model</div>
					<div class="mt-1 text-lg tracking-tight">
						{task ? task.model_name || 'yolo11n' : 'Loading...'}
					</div>
				</div>
				<div class="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
					<div class="text-sm font-semibold text-muted-foreground">Duration</div>
					<div class="mt-1 text-lg tracking-tight">{task ? task.duration || '--:--' : '--:--'}</div>
				</div>
				<div class="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
					<div class="text-sm font-semibold text-muted-foreground">Output Format</div>
					<div class="mt-1 text-lg tracking-tight">{task ? task.format || 'mp4' : 'mp4'}</div>
				</div>
			</div>
		</div>
	</div>
</div>
