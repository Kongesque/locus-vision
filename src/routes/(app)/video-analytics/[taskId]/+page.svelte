<script lang="ts">
	import { page } from '$app/stores';
	import { AspectRatio } from '$lib/components/ui/aspect-ratio/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { ChevronLeft, Loader2, Download, FileJson, Activity } from '@lucide/svelte';
	import { onMount, onDestroy, tick } from 'svelte';

	let { data } = $props();

	let taskId = $derived(data.taskId);
	let task = $derived(data.task as any);

	let videoSrc = $state<string | null>(null);
	let status = $state<'loading' | 'processing' | 'ready' | 'error'>('loading');
	let pollInterval: NodeJS.Timeout;

	// Video element ref
	let videoEl = $state<HTMLVideoElement | null>(null);

	// Timeline data
	let timelineData = $state<{ timestamp: number; count: number }[]>([]);
	let timelineCanvas = $state<HTMLCanvasElement | null>(null);
	let hoveredTime = $state<number | null>(null);
	let hoveredCount = $state<number | null>(null);
	let currentVideoTime = $state(0);
	let videoDuration = $state(0);
	let timelineLoaded = $state(false);

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

	// Fetch timeline data when status is ready
	$effect(() => {
		if (status === 'ready' && !timelineLoaded) {
			fetchTimelineData();
		}
	});

	// Draw timeline when data or canvas changes
	$effect(() => {
		if (timelineCanvas && timelineData.length > 0) {
			drawTimeline();
		}
	});

	// Redraw on video time update to show playhead
	$effect(() => {
		if (timelineCanvas && timelineData.length > 0 && currentVideoTime >= 0) {
			drawTimeline();
		}
	});

	async function fetchTimelineData() {
		try {
			const res = await fetch(`http://localhost:8000/api/video/${taskId}/data`);
			if (!res.ok) return;
			const json = await res.json();
			if (json.frames && Array.isArray(json.frames)) {
				timelineData = json.frames.map((f: any) => ({
					timestamp: f.timestamp,
					count: f.current_total_count ?? 0
				}));
				timelineLoaded = true;
			}
		} catch (e) {
			console.error('Failed to fetch timeline data', e);
		}
	}

	function drawTimeline() {
		if (!timelineCanvas) return;
		const canvas = timelineCanvas;
		const ctx = canvas.getContext('2d');
		if (!ctx) return;

		// Set canvas resolution to match display size
		const rect = canvas.getBoundingClientRect();
		const dpr = window.devicePixelRatio || 1;
		canvas.width = rect.width * dpr;
		canvas.height = rect.height * dpr;
		ctx.scale(dpr, dpr);

		const w = rect.width;
		const h = rect.height;
		const padding = { top: 20, right: 16, bottom: 28, left: 40 };
		const chartW = w - padding.left - padding.right;
		const chartH = h - padding.top - padding.bottom;

		// Clear
		ctx.clearRect(0, 0, w, h);

		if (timelineData.length === 0) return;

		const maxCount = Math.max(...timelineData.map((d) => d.count), 1);
		const maxTime = timelineData[timelineData.length - 1].timestamp || 1;

		// Draw grid lines
		ctx.strokeStyle = 'rgba(255,255,255,0.06)';
		ctx.lineWidth = 1;
		const gridLines = 4;
		for (let i = 0; i <= gridLines; i++) {
			const y = padding.top + (chartH / gridLines) * i;
			ctx.beginPath();
			ctx.moveTo(padding.left, y);
			ctx.lineTo(w - padding.right, y);
			ctx.stroke();
		}

		// Y-axis labels
		ctx.fillStyle = 'rgba(255,255,255,0.4)';
		ctx.font = '10px system-ui, sans-serif';
		ctx.textAlign = 'right';
		ctx.textBaseline = 'middle';
		for (let i = 0; i <= gridLines; i++) {
			const val = Math.round(maxCount - (maxCount / gridLines) * i);
			const y = padding.top + (chartH / gridLines) * i;
			ctx.fillText(String(val), padding.left - 6, y);
		}

		// X-axis labels
		ctx.textAlign = 'center';
		ctx.textBaseline = 'top';
		const xLabels = 6;
		for (let i = 0; i <= xLabels; i++) {
			const t = (maxTime / xLabels) * i;
			const x = padding.left + (chartW / xLabels) * i;
			const mins = Math.floor(t / 60);
			const secs = Math.floor(t % 60);
			ctx.fillText(`${mins}:${secs.toString().padStart(2, '0')}`, x, h - padding.bottom + 8);
		}

		// Draw area fill
		const gradient = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartH);
		gradient.addColorStop(0, 'rgba(59, 130, 246, 0.35)');
		gradient.addColorStop(1, 'rgba(59, 130, 246, 0.02)');

		ctx.beginPath();
		ctx.moveTo(padding.left, padding.top + chartH);
		for (let i = 0; i < timelineData.length; i++) {
			const x = padding.left + (timelineData[i].timestamp / maxTime) * chartW;
			const y = padding.top + chartH - (timelineData[i].count / maxCount) * chartH;
			if (i === 0) ctx.lineTo(x, y);
			else ctx.lineTo(x, y);
		}
		ctx.lineTo(
			padding.left + (timelineData[timelineData.length - 1].timestamp / maxTime) * chartW,
			padding.top + chartH
		);
		ctx.closePath();
		ctx.fillStyle = gradient;
		ctx.fill();

		// Draw line
		ctx.beginPath();
		ctx.strokeStyle = 'rgba(59, 130, 246, 0.9)';
		ctx.lineWidth = 2;
		ctx.lineJoin = 'round';
		for (let i = 0; i < timelineData.length; i++) {
			const x = padding.left + (timelineData[i].timestamp / maxTime) * chartW;
			const y = padding.top + chartH - (timelineData[i].count / maxCount) * chartH;
			if (i === 0) ctx.moveTo(x, y);
			else ctx.lineTo(x, y);
		}
		ctx.stroke();

		// Draw playhead
		if (videoDuration > 0) {
			const playX = padding.left + (currentVideoTime / maxTime) * chartW;
			if (playX >= padding.left && playX <= padding.left + chartW) {
				ctx.beginPath();
				ctx.strokeStyle = 'rgba(255, 255, 255, 0.7)';
				ctx.lineWidth = 1.5;
				ctx.setLineDash([4, 3]);
				ctx.moveTo(playX, padding.top);
				ctx.lineTo(playX, padding.top + chartH);
				ctx.stroke();
				ctx.setLineDash([]);

				// Small triangle at top
				ctx.fillStyle = 'rgba(255,255,255,0.8)';
				ctx.beginPath();
				ctx.moveTo(playX - 4, padding.top);
				ctx.lineTo(playX + 4, padding.top);
				ctx.lineTo(playX, padding.top + 6);
				ctx.closePath();
				ctx.fill();
			}
		}

		// Draw hover indicator
		if (hoveredTime !== null) {
			const hoverX = padding.left + (hoveredTime / maxTime) * chartW;
			ctx.beginPath();
			ctx.strokeStyle = 'rgba(59, 130, 246, 0.6)';
			ctx.lineWidth = 1;
			ctx.setLineDash([2, 2]);
			ctx.moveTo(hoverX, padding.top);
			ctx.lineTo(hoverX, padding.top + chartH);
			ctx.stroke();
			ctx.setLineDash([]);

			// Dot at the data point
			if (hoveredCount !== null) {
				const dotY = padding.top + chartH - (hoveredCount / maxCount) * chartH;
				ctx.beginPath();
				ctx.arc(hoverX, dotY, 4, 0, Math.PI * 2);
				ctx.fillStyle = 'rgb(59, 130, 246)';
				ctx.fill();
				ctx.strokeStyle = 'white';
				ctx.lineWidth = 2;
				ctx.stroke();
			}
		}
	}

	function handleTimelineClick(e: MouseEvent) {
		if (!timelineCanvas || !videoEl || timelineData.length === 0) return;
		const rect = timelineCanvas.getBoundingClientRect();
		const padding = { left: 40, right: 16 };
		const chartW = rect.width - padding.left - padding.right;
		const x = e.clientX - rect.left - padding.left;
		if (x < 0 || x > chartW) return;

		const maxTime = timelineData[timelineData.length - 1].timestamp || 1;
		const targetTime = (x / chartW) * maxTime;
		videoEl.currentTime = targetTime;
	}

	function handleTimelineHover(e: MouseEvent) {
		if (!timelineCanvas || timelineData.length === 0) return;
		const rect = timelineCanvas.getBoundingClientRect();
		const padding = { left: 40, right: 16 };
		const chartW = rect.width - padding.left - padding.right;
		const x = e.clientX - rect.left - padding.left;
		if (x < 0 || x > chartW) {
			hoveredTime = null;
			hoveredCount = null;
			return;
		}

		const maxTime = timelineData[timelineData.length - 1].timestamp || 1;
		hoveredTime = (x / chartW) * maxTime;

		// Find nearest data point
		let nearest = timelineData[0];
		let minDist = Infinity;
		for (const d of timelineData) {
			const dist = Math.abs(d.timestamp - hoveredTime);
			if (dist < minDist) {
				minDist = dist;
				nearest = d;
			}
		}
		hoveredCount = nearest.count;
	}

	function handleTimelineLeave() {
		hoveredTime = null;
		hoveredCount = null;
	}

	function formatTime(seconds: number): string {
		const m = Math.floor(seconds / 60);
		const s = Math.floor(seconds % 60);
		return `${m}:${s.toString().padStart(2, '0')}`;
	}

	let taskProgress = $state(0);

	async function checkStatus() {
		if (status === 'ready') return;
		try {
			const res = await fetch(`http://localhost:8000/api/video/${taskId}/status`);
			if (res.ok) {
				const data = await res.json();
				if (data.status === 'completed') {
					videoSrc = `http://localhost:8000/api/video/${taskId}/result`;
					status = 'ready';
					taskProgress = 100;
					stopPolling();
				} else if (data.status === 'failed') {
					status = 'error';
					stopPolling();
				} else if (data.status === 'processing') {
					status = 'processing';
					taskProgress = data.progress || 0;
				} else {
					status = 'processing';
				}
			}
		} catch (e) {
			console.error('Error checking status', e);
		}
	}

	function startPolling() {
		if (status === 'ready' || status === 'error') return;
		checkStatus();
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
			{#if status === 'ready'}
				<Button size="sm" class="gap-2" href={videoSrc} download>
					<Download class="h-4 w-4" />
					Export Video
				</Button>
			{/if}
			<div class="ml-4 flex items-center gap-2">
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
							bind:this={videoEl}
							src={videoSrc}
							class="h-full w-full object-contain"
							controls
							autoplay
							loop
							playsinline
							crossorigin="anonymous"
							ontimeupdate={() => {
								if (videoEl) currentVideoTime = videoEl.currentTime;
							}}
							onloadedmetadata={() => {
								if (videoEl) videoDuration = videoEl.duration;
							}}
						></video>
					{:else if status === 'processing' || status === 'loading'}
						<div
							class="flex h-full flex-col items-center justify-center gap-4 text-muted-foreground"
						>
							<Loader2 class="h-8 w-8 animate-spin" />
							<p>Processing video task... {taskProgress > 0 ? `${taskProgress}%` : ''}</p>
							{#if taskProgress > 0}
								<div class="mx-auto h-1.5 w-48 overflow-hidden rounded-full bg-white/10">
									<div
										class="h-full rounded-full bg-blue-500 transition-all duration-500 ease-out"
										style="width: {taskProgress}%"
									></div>
								</div>
							{/if}
							<p class="text-xs opacity-70">
								This typically takes 10-30 seconds depending on video length.
							</p>
						</div>
					{/if}
				</AspectRatio>
			</div>

			<!-- Interactive Activity Timeline -->
			{#if status === 'ready' && timelineData.length > 0}
				<div class="overflow-hidden rounded-lg border bg-card shadow-sm">
					<div class="flex items-center justify-between border-b bg-muted/30 px-4 py-3">
						<div class="flex items-center gap-2">
							<Activity class="h-4 w-4 text-blue-400" />
							<h3 class="text-sm font-semibold tracking-tight text-muted-foreground">
								Activity Timeline
							</h3>
						</div>
						<div class="flex items-center gap-3 text-xs text-muted-foreground">
							{#if hoveredTime !== null}
								<span class="font-mono text-blue-400">
									{formatTime(hoveredTime)} · {hoveredCount} objects
								</span>
							{:else}
								<span>Click to jump · Hover for details</span>
							{/if}
						</div>
					</div>
					<div class="p-3">
						<canvas
							bind:this={timelineCanvas}
							class="h-[120px] w-full cursor-crosshair rounded"
							onclick={handleTimelineClick}
							onmousemove={handleTimelineHover}
							onmouseleave={handleTimelineLeave}
							aria-label="Activity timeline chart - click to jump to time"
						></canvas>
					</div>
				</div>
			{/if}

			<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
				<div class="grid grid-cols-2 gap-4 md:col-span-2">
					<div class="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
						<div class="text-sm font-semibold text-muted-foreground">Detection Model</div>
						<div class="mt-1 text-2xl font-bold tracking-tight">
							{task ? task.model_name || 'yolo11n' : 'Loading...'}
						</div>
					</div>
					<div class="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
						<div class="text-sm font-semibold text-muted-foreground">Duration Analyzed</div>
						<div class="mt-1 text-2xl font-bold tracking-tight">
							{task ? task.duration || '--:--' : '--:--'}
						</div>
					</div>

					<div
						class="col-span-2 flex flex-col gap-2 rounded-lg border bg-card p-4 text-card-foreground shadow-sm"
					>
						<div class="text-sm font-semibold text-muted-foreground">Analysis Context</div>
						<div class="text-sm">
							Processed using high-accuracy tracking at 12fps. Export data to view raw JSON
							detections for every frame, tracked via DeepSort.
						</div>
						<div class="mt-2">
							<Button
								variant="secondary"
								size="sm"
								class="gap-2"
								href={`http://localhost:8000/api/video/${taskId}/data`}
								download
							>
								<FileJson class="h-4 w-4" />
								Export Raw Data (JSON)
							</Button>
						</div>
					</div>
				</div>

				<div
					class="flex min-h-[200px] flex-col overflow-hidden rounded-lg border bg-card shadow-sm"
				>
					<div class="border-b bg-muted/30 p-4">
						<h3 class="text-sm font-semibold tracking-tight text-muted-foreground">
							Detected Activity Summary
						</h3>
					</div>
					<div class="flex flex-1 flex-col p-4">
						{#if status === 'ready' && task}
							<div class="mb-4 flex flex-col items-center justify-center border-b pb-4">
								<div class="mb-1 text-sm text-muted-foreground">Total Unique Objects</div>
								<div class="text-5xl font-bold text-primary">{task.total_count || 0}</div>
							</div>

							<!-- Render Zone Counts if they exist -->
							{@const parsedZoneCounts = task.zone_counts ? JSON.parse(task.zone_counts) : null}
							{#if parsedZoneCounts && Object.keys(parsedZoneCounts).length > 0}
								<div class="grid w-full grid-cols-2 gap-2">
									{#each Object.entries(parsedZoneCounts) as [zoneId, count]}
										<div class="rounded bg-muted/30 p-2 text-center">
											<div class="truncate text-xs text-muted-foreground" title={zoneId}>
												{zoneId.length > 8 ? `Zone ${zoneId.slice(0, 4)}` : zoneId}
											</div>
											<div class="text-xl font-bold">{count}</div>
										</div>
									{/each}
								</div>
							{:else}
								<div class="mt-4 text-center text-sm text-muted-foreground">
									No zones defined for this task.
								</div>
							{/if}
						{:else}
							<div
								class="flex flex-1 flex-col items-center justify-center text-center text-sm text-muted-foreground"
							>
								Waiting for analysis to complete...
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
