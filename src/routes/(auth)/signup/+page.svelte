<script lang="ts">
	import { enhance } from '$app/forms';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Eye, EyeOff } from '@lucide/svelte';
	import Echo from '$lib/components/svg/echo.svelte';

	let { form } = $props();

	let showPassword = $state(false);
	let loading = $state(false);
</script>

<svelte:head>
	<title>Sign Up · Locus</title>
</svelte:head>

<div class="flex min-h-svh flex-col">
	<!-- Logo -->
	<div class="p-6">
		<Echo class="size-6" />
	</div>

	<!-- Form centered -->
	<div class="flex flex-1 items-center justify-center px-6 pb-20">
		<div class="w-full max-w-md space-y-6">
			<h1 class="text-center text-2xl font-semibold">Sign up to Locus Vision</h1>

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
				<div class="space-y-2">
					<label for="name" class="text-sm font-semibold cursor-pointer">Name</label>
					<Input
						id="name"
						name="name"
						type="text"
						placeholder="Enter Your Full Name"
						value={form?.name ?? ''}
						class="rounded-none border-0 border-b border-border bg-transparent px-0 shadow-none placeholder:text-muted-foreground focus-visible:border-foreground focus-visible:ring-0 dark:bg-transparent cursor-text"
					/>
				</div>

				<div class="space-y-2">
					<label for="email" class="text-sm font-semibold cursor-pointer">Email</label>
					<Input
						id="email"
						name="email"
						type="email"
						placeholder="Enter Your Email"
						value={form?.email ?? ''}
						class="rounded-none border-0 border-b border-border bg-transparent px-0 shadow-none placeholder:text-muted-foreground focus-visible:border-foreground focus-visible:ring-0 dark:bg-transparent cursor-text"
					/>
				</div>

				<div class="space-y-2">
					<label for="password" class="text-sm font-semibold cursor-pointer">Password</label>
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
							class="absolute top-1/2 right-0 -translate-y-1/2 text-muted-foreground hover:text-foreground cursor-pointer"
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
					class="w-full rounded-full bg-muted text-foreground shadow-none hover:bg-muted/80 cursor-pointer"
				>
					{loading ? 'Creating Account...' : 'Create Account'}
				</Button>
			</form>

			<p class="text-center text-sm">
				Already have an account? <a
					href="/login"
					class="font-medium text-foreground underline hover:text-foreground/80">Sign in</a
				>
			</p>
		</div>
	</div>
</div>
