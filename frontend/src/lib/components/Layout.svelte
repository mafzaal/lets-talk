<script lang="ts">
	import type { Snippet } from 'svelte';

	import * as Sidebar from '$lib/components/ui/sidebar';
	import AppSidebar from '$lib/components/app-sidebar.svelte';
	import SystemStatus from './SystemStatus.svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();
</script>

<div class="flex h-screen">
	<!-- Sidebar using shadcn-svelte -->
	<Sidebar.Provider>
		<AppSidebar />
		<!-- Main content area -->
		<main class="flex-1 overflow-auto p-6">
			{@render children()}
		</main>
	</Sidebar.Provider>
</div>
