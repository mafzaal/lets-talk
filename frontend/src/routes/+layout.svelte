<script lang="ts">
	import '../app.css';
	import Layout from '$lib/components/Layout.svelte';
	import { page } from '$app/state';

	let { children } = $props();

	// Only show layout for dashboard-related pages
	let showLayout = $derived(
		page.url.pathname.startsWith('/dashboard') ||
			page.url.pathname.startsWith('/jobs') ||
			page.url.pathname.startsWith('/analytics') ||
			page.url.pathname.startsWith('/activity')
	);
</script>

{#if showLayout}
	<Layout>
		{@render children()}
	</Layout>
{:else}
	{@render children()}
{/if}
