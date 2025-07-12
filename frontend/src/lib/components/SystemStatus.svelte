<script lang="ts">
	import { onMount } from 'svelte';
	import { apiClient, type HealthStatus } from '$lib/api';

	let state = {
		health: null as HealthStatus | null,
		loading: true,
		error: null as string | null
	};

	function formatLocalTime(iso: string | undefined) {
		if (!iso) return '';
		const date = new Date(iso);
		if (isNaN(date.getTime())) return iso;
		return date.toLocaleString();
	}

	onMount(async () => {
		state.loading = true;
		state.error = null;
		try {
			const data = await apiClient.getHealth();
			state.health = data;
		} catch (e) {
			state.error = e instanceof Error ? e.message : 'Unknown error';
			state.health = null;
		} finally {
			state.loading = false;
		}
	});
</script>

<div class="flex items-center space-x-2 text-sm text-slate-400 group relative">
	<div
		class="w-2 h-2 rounded-full"
		class:bg-green-500={state.health?.status === 'healthy' && !state.error}
		class:bg-red-500={state.health?.status !== 'healthy' || state.error}
		class:bg-gray-400={state.loading}
	></div>
	<span>
		{#if state.loading}
			Checking...
		{:else if state.error}
			System Error
		{:else if state.health?.status === 'healthy'}
			System Online
		{:else}
			System Issue
		{/if}
	</span>
	<!-- Tooltip on hover -->
	<div
		class="absolute left-1/2 -translate-x-1/2 top-full mt-2 z-10 hidden group-hover:block bg-slate-800 text-white text-xs rounded shadow-lg px-4 py-2 min-w-[220px] whitespace-pre-line border border-slate-700"
	>
		{#if state.loading}
			Checking system health...
		{:else if state.error}
			Error: {state.error}
		{:else if state.health}
			<b>Status:</b>
			{state.health.status}
			<br /><b>Scheduler:</b>
			{state.health.scheduler_status}
			<br /><b>Version:</b>
			{state.health.version}
			<br /><b>Timestamp:</b>
			{formatLocalTime(state.health.timestamp)}
		{:else}
			No data.
		{/if}
	</div>
</div>

<style>
	.group:hover .group-hover\:block {
		display: block;
	}
</style>
