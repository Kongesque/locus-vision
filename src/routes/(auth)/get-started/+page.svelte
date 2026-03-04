<script lang="ts">
	import { enhance } from '$app/forms';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Eye, EyeOff, Info } from '@lucide/svelte';
	import Echo from '$lib/components/svg/echo.svelte';

	let { form } = $props();

	let showPassword = $state(false);
	let loading = $state(false);
</script>

<svelte:head>
	<title>Get Started · Locus</title>
</svelte:head>

<div class="flex min-h-svh flex-col">
	<!-- Logo -->
	<div class="p-6">
		<Echo class="size-6" />
	</div>

	<!-- Form centered -->
	<div class="flex flex-1 items-center justify-center px-6 pb-20">
		<div class="w-full max-w-md space-y-4">
			<h1 class="text-center text-2xl font-semibold">Get started with Locus Vision</h1>
			<p class="flex items-center justify-center gap-2 text-center text-sm text-muted-foreground">
				<Info class="size-3" />
				Your data stays local. Nothing is sent to external servers.
			</p>

			{#if form?.error}
				<p class="rounded-lg bg-destructive/10 px-4 py-2 text-center text-sm text-destructive">
					{form.error}
				</p>
			{/if}

			<form
				method="POST"
				class="space-y-4"
				use:enhance={() => {
					loading = true;
					return async ({ update }) => {
						loading = false;
						await update();
					};
				}}
			>
				<div>
					<label for="name" class="text-sm font-semibold">Name</label>
					<Input
						id="name"
						name="name"
						type="text"
						placeholder="Enter Your Full Name"
						value={form?.name ?? ''}
						class="rounded-none border-0 border-b border-border bg-transparent px-0 shadow-none placeholder:text-muted-foreground focus-visible:border-foreground focus-visible:ring-0 dark:bg-transparent"
					/>
				</div>

				<div>
					<label for="email" class="text-sm font-semibold">Email</label>
					<Input
						id="email"
						name="email"
						type="email"
						placeholder="Enter Your Email"
						value={form?.email ?? ''}
						class="rounded-none border-0 border-b border-border bg-transparent px-0 shadow-none placeholder:text-muted-foreground focus-visible:border-foreground focus-visible:ring-0 dark:bg-transparent"
					/>
				</div>

				<div>
					<label for="password" class="text-sm font-semibold">Password</label>
					<div class="relative">
						<Input
							id="password"
							name="password"
							type={showPassword ? 'text' : 'password'}
							placeholder="Enter Your Password"
							class="rounded-none border-0 border-b border-border bg-transparent px-0 pr-8 shadow-none placeholder:text-muted-foreground focus-visible:border-foreground focus-visible:ring-0 dark:bg-transparent"
						/>
						<button
							type="button"
							class="absolute top-1/2 right-0 -translate-y-1/2 text-muted-foreground hover:text-foreground"
							onclick={() => (showPassword = !showPassword)}
						>
							{#if showPassword}
								<Eye class="size-4" />
							{:else}
								<EyeOff class="size-4" />
							{/if}
						</button>
					</div>
				</div>

				<Button
					type="submit"
					disabled={loading}
					class="w-full rounded-full bg-muted text-foreground shadow-none hover:bg-muted/80"
				>
					{loading ? 'Setting up...' : 'Create Admin Account'}
				</Button>
			</form>
		</div>
	</div>
</div>
