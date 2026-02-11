<script lang="ts">
	import { Search } from '@lucide/svelte';
	import {
		InputGroup,
		InputGroupAddon,
		InputGroupInput
	} from '$lib/components/ui/input-group/index.js';

	let { value = $bindable(), placeholder = 'Search history' } = $props();
</script>

<InputGroup>
	<InputGroupAddon>
		<Search class="size-4 text-muted-foreground" />
	</InputGroupAddon>
	<InputGroupInput {placeholder} bind:value />
</InputGroup>
