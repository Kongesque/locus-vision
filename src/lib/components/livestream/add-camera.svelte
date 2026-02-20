<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Tabs from '$lib/components/ui/tabs/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Plus } from '@lucide/svelte';
	import { goto } from '$app/navigation';
	import { videoStore } from '$lib/stores/video.svelte';

	let open = $state(false);
	let activeTab = $state('rtsp');
	let isConnecting = $state(false);

	// RTSP form fields
	let rtspName = $state('');
	let rtspUrl = $state('');

	// Webcam form fields
	let webcamName = $state('');
	let selectedDeviceId = $state<string | undefined>(undefined);

	async function handleConnect() {
		try {
			isConnecting = true;
			const cameraId = crypto.randomUUID();
			const config = {
				id: cameraId,
				name: activeTab === 'webcam' ? webcamName || 'Webcam' : rtspName || 'RTSP Stream',
				type: activeTab,
				url: activeTab === 'rtsp' ? rtspUrl : null,
				device_id: activeTab === 'webcam' ? selectedDeviceId : null
			};

			const response = await fetch('http://localhost:8000/api/cameras/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(config)
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || 'Failed to create camera');
			}

			// Sync with global store so create page knows what we're editing
			videoStore.setVideoType(activeTab as 'rtsp' | 'stream'); // temporarily cast to valid types
			if (activeTab === 'rtsp') videoStore.setVideoUrl(rtspUrl);
			else videoStore.setVideoType('stream');

			open = false;
			goto(`/create/${cameraId}`);
		} catch (err) {
			console.error(err);
			alert('Failed to connect camera: ' + (err instanceof Error ? err.message : String(err)));
		} finally {
			isConnecting = false;
		}
	}
</script>

<Dialog.Root bind:open>
	<Dialog.Trigger>
		{#snippet child({ props })}
			<Button {...props} variant="default" class="cursor-pointer">
				<Plus class="size-4" />
				Add Camera
			</Button>
		{/snippet}
	</Dialog.Trigger>

	<Dialog.Content class="sm:max-w-[500px]">
		<Dialog.Header>
			<Dialog.Title>Add Camera</Dialog.Title>
			<Dialog.Description>Connect a new camera via RTSP stream or local webcam.</Dialog.Description>
		</Dialog.Header>

		<Tabs.Root bind:value={activeTab} class="w-full">
			<Tabs.List class="grid w-full grid-cols-2">
				<Tabs.Trigger value="rtsp" class="cursor-pointer">RTSP / HTTP</Tabs.Trigger>
				<Tabs.Trigger value="webcam" class="cursor-pointer">Webcam</Tabs.Trigger>
			</Tabs.List>

			<Tabs.Content value="rtsp" class="space-y-4 py-4">
				<div class="space-y-2">
					<Label for="rtsp-name">Camera Name</Label>
					<Input
						id="rtsp-name"
						placeholder="e.g. Front Door"
						bind:value={rtspName}
						disabled={isConnecting}
					/>
				</div>
				<div class="space-y-2">
					<Label for="rtsp-url">Stream URL</Label>
					<Input
						id="rtsp-url"
						placeholder="rtsp://admin:password@192.168.1.10:554/stream"
						bind:value={rtspUrl}
						disabled={isConnecting}
					/>
				</div>
			</Tabs.Content>

			<Tabs.Content value="webcam" class="space-y-4 py-4">
				<div class="space-y-2">
					<Label for="webcam-name">Camera Name</Label>
					<Input
						id="webcam-name"
						placeholder="e.g. Desk Webcam"
						bind:value={webcamName}
						disabled={isConnecting}
					/>
				</div>
				<div class="space-y-2">
					<Label for="device">Device</Label>
					<Select.Root type="single" bind:value={selectedDeviceId} disabled={isConnecting}>
						<Select.Trigger id="device" placeholder="Select a device" />
						<Select.Content>
							<Select.Item value="default">Default Camera</Select.Item>
							<!-- TODO: Populate with real devices from navigator.mediaDevices.enumerateDevices() -->
						</Select.Content>
					</Select.Root>
				</div>

				<div
					class="relative flex aspect-video items-center justify-center overflow-hidden rounded-md bg-black"
				>
					<!-- TODO: Implement webcam preview -->
					<!-- - Request camera access when webcam tab is active -->
					<!-- - Display live video feed in this area -->
					<!-- - Handle permission errors gracefully -->
					<div class="text-sm text-muted-foreground">Camera preview will appear here</div>
				</div>
			</Tabs.Content>
		</Tabs.Root>

		<Dialog.Footer>
			<Button
				variant="outline"
				class="cursor-pointer"
				onclick={() => (open = false)}
				disabled={isConnecting}>Cancel</Button
			>
			<Button class="cursor-pointer" onclick={handleConnect} disabled={isConnecting}>
				{isConnecting ? 'Connecting...' : 'Connect'}
			</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
