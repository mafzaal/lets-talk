<script lang="ts">
	import '../app.css';
	import * as Sidebar from '$lib/components/ui/sidebar';
	import AppSidebar from '$lib/components/app-sidebar.svelte';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import { Toaster } from 'svelte-sonner';
	import { themeStore } from '$lib/stores/theme';
	import { onMount } from 'svelte';

	let { children } = $props();

	// Initialize theme on mount
	onMount(() => {
		themeStore.init();
	});
</script>

<!-- Sidebar using shadcn-svelte -->
<Sidebar.Provider>
	<AppSidebar />
	<Sidebar.Inset>
		<header class="flex h-16 shrink-0 items-center gap-2 border-b px-4 justify-between">
			<Sidebar.Trigger class="-ml-1" />
			<ThemeToggle />
		</header>
		<!-- Main content area -->
		<main class="flex flex-1 flex-col gap-4 p-4">
			{@render children()}
		</main>
	</Sidebar.Inset>
</Sidebar.Provider>

<Toaster theme={$themeStore} position="top-right" />
