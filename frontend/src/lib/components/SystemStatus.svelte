<script lang="ts">
	import { onMount } from 'svelte';
	import { apiClient, type HealthStatus } from '$lib/api';
	import * as Tooltip from '$lib/components/ui/tooltip';

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

<Tooltip.Provider>
	<Tooltip.Root>
		<Tooltip.Trigger>
			<div class="flex items-center space-x-2 text-sm group relative">
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
			</div>
		</Tooltip.Trigger>
		<Tooltip.Content>
			<div>
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
		</Tooltip.Content>
	</Tooltip.Root>
</Tooltip.Provider>

<style>
</style>
