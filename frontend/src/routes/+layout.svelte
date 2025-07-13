<script lang="ts">
	import '../app.css';
	import Layout from '$lib/components/Layout.svelte';
	import { page } from '$app/state';
	import { Toaster } from 'svelte-sonner';
	import { themeStore } from '$lib/stores/theme';
	import { onMount } from 'svelte';

	let { children } = $props();

	// Initialize theme on mount
	onMount(() => {
		themeStore.init();
	});

	// Only show layout for dashboard-related pages
	let showLayout = $derived(
		page.url.pathname.startsWith('/dashboard') ||
			page.url.pathname.startsWith('/jobs') ||
			page.url.pathname.startsWith('/analytics') ||
			page.url.pathname.startsWith('/activity') ||
			page.url.pathname.startsWith('/settings')
	);
</script>

{#if showLayout}
	<Layout>
		{@render children()}
	</Layout>
{:else}
	{@render children()}
{/if}

<Toaster theme={$themeStore} position="top-right" />
