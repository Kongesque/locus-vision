<script lang="ts">
	import { SidebarTrigger } from '$lib/components/ui/sidebar/index.js';
	import { cn } from '$lib/utils.js';

	let { class: className = undefined, cursorClass = undefined } = $props();
</script>

<header
	class={cn(
		'sticky top-0 z-20 flex h-12 shrink-0 items-center justify-between border-b bg-background px-4',
		className
	)}
>
	<div class="flex items-center gap-4">
		<SidebarTrigger class={cn('-ml-2.5', cursorClass)} />
	</div>
</header>
