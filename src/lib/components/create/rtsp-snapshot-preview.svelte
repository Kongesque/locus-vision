<script lang="ts">
	import DrawingCanvas, { type Point, type Zone } from './drawing-canvas.svelte';
	import { onMount } from 'svelte';

	interface Props {
		url: string;
		zones: Zone[];
		selectedZoneId: string | null;
		drawingMode: 'polygon' | 'line';
		onZoneCreated: (points: Point[]) => void;
		onZoneSelected: (id: string | null) => void;
		onZoneUpdated: (id: string, newPoints: Point[]) => void;
	}

	let {
		url,
		zones,
		selectedZoneId,
		drawingMode,
		onZoneCreated,
		onZoneSelected,
		onZoneUpdated
	}: Props = $props();

	let containerRef: HTMLDivElement | undefined = $state();
	let imgRef: HTMLImageElement | undefined = $state();
	let snapshotSrc = $state<string | null>(null);
	let isLoading = $state(false);
	let error = $state<string | null>(null);
	let imageDims = $state<{
		width: number;
		height: number;
		naturalWidth: number;
		naturalHeight: number;
	} | null>(null);

	async function fetchSnapshot() {
		if (!url) return;
		try {
			isLoading = true;
			error = null;

			const res = await fetch('http://localhost:8000/api/cameras/preview', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ url })
			});

			if (!res.ok) {
				const data = await res.json();
				throw new Error(data.detail || 'Failed to fetch snapshot');
			}

			const data = await res.json();
			snapshotSrc = data.image;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Snapshot failed';
		} finally {
			isLoading = false;
		}
	}

	function updateDims() {
		if (!imgRef || !containerRef) return;

		const { width: cw, height: ch } = containerRef.getBoundingClientRect();
		const nw = imgRef.naturalWidth;
		const nh = imgRef.naturalHeight;

		if (nw === 0 || nh === 0) return;

		const containerRatio = cw / ch;
		const imageRatio = nw / nh;

		let displayW = cw;
		let displayH = ch;

		if (containerRatio > imageRatio) {
			displayW = ch * imageRatio;
		} else {
			displayH = cw / imageRatio;
		}

		imageDims = {
			width: displayW,
			height: displayH,
			naturalWidth: nw,
			naturalHeight: nh
		};
	}

	onMount(() => {
		fetchSnapshot();

		const observer = new ResizeObserver(updateDims);
		if (containerRef) observer.observe(containerRef);

		return () => observer.disconnect();
	});
</script>

<div
	bind:this={containerRef}
	class="relative flex h-full w-full items-center justify-center overflow-hidden rounded-lg bg-black"
>
	{#if isLoading}
		<div class="animate-pulse text-sm text-muted-foreground">Fetching stream snapshot...</div>
	{:else if error}
		<div class="flex flex-col items-center gap-3 text-center">
			<p class="text-sm text-red-500">{error}</p>
			<button
				class="cursor-pointer rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-zinc-800"
				onclick={fetchSnapshot}
			>
				Retry
			</button>
		</div>
	{:else if snapshotSrc}
		<img
			bind:this={imgRef}
			src={snapshotSrc}
			alt="RTSP snapshot"
			class="pointer-events-none max-h-full max-w-full object-contain"
			onload={updateDims}
		/>

		{#if imageDims}
			<div
				class="absolute z-10 flex items-center justify-center"
				style="width: {imageDims.width}px; height: {imageDims.height}px;"
			>
				<DrawingCanvas
					width={imageDims.width}
					height={imageDims.height}
					videoWidth={imageDims.naturalWidth}
					videoHeight={imageDims.naturalHeight}
					{zones}
					{selectedZoneId}
					{drawingMode}
					{onZoneCreated}
					{onZoneSelected}
					{onZoneUpdated}
				/>
			</div>
		{/if}

		<!-- Refresh button -->
		<button
			class="absolute right-2 bottom-2 z-20 cursor-pointer rounded-md bg-black/60 px-2.5 py-1.5 text-xs text-white backdrop-blur-sm transition-colors hover:bg-black/80"
			onclick={fetchSnapshot}
		>
			↻ Refresh
		</button>
	{:else}
		<div class="text-sm text-muted-foreground">No stream URL provided</div>
	{/if}
</div>
