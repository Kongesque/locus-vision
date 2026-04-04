<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Sun, Moon, Monitor } from '@lucide/svelte';
	import { setMode, resetMode } from 'mode-watcher';
</script>

<Card.Root>
	<Card.Header>
		<Card.Title class="text-lg">Theme</Card.Title>
		<Card.Description>Customize the appearance of the application</Card.Description>
	</Card.Header>
	<Card.Content>
		<div class="flex flex-wrap items-center gap-3">
			<Button
				variant="outline"
				class="flex items-center gap-2 cursor-pointer"
				onclick={() => setMode('light')}
			>
				<Sun class="size-4" />
				Light
			</Button>
			<Button variant="outline" class="flex items-center gap-2 cursor-pointer" onclick={() => setMode('dark')}>
				<Moon class="size-4" />
				Dark
			</Button>
			<Button variant="outline" class="flex items-center gap-2 cursor-pointer" onclick={() => resetMode()}>
				<Monitor class="size-4" />
				System
			</Button>
		</div>
	</Card.Content>
</Card.Root>
