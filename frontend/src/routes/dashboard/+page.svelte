<script lang="ts">
	import { onMount } from 'svelte';
	import { apiClient, type SchedulerStats, type PipelineReport } from '$lib/api';
	import * as Card from '$lib/components/ui/card';
	import {
		Activity,
		AlertCircle,
		CheckCircle,
		Clock,
		TrendingUp,
		Users,
		Play
	} from 'lucide-svelte';
	import { Root } from '$lib/components/ui/button';
	import { Description } from 'formsnap';

	let stats: SchedulerStats | null = $state(null);
	let reports: PipelineReport[] = $state([]);
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		try {
			const [schedulerStats, pipelineReports] = await Promise.all([
				apiClient.getSchedulerStats(),
				apiClient.getPipelineReports()
			]);

			stats = schedulerStats;
			reports = pipelineReports.reports;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load dashboard data';
		} finally {
			loading = false;
		}
	});

	function formatDateTime(dateString: string | undefined) {
		if (!dateString) return 'Never';
		return new Date(dateString).toLocaleString();
	}

	function getStatusColor(status: string) {
		switch (status?.toLowerCase()) {
			case 'success':
				return 'text-green-400';
			case 'failed':
				return 'text-red-400';
			case 'running':
				return 'text-blue-400';
			default:
				return 'text-slate-400';
		}
	}

	function getStatusIcon(status: string) {
		switch (status?.toLowerCase()) {
			case 'success':
				return CheckCircle;
			case 'failed':
				return AlertCircle;
			case 'running':
				return Play;
			default:
				return Clock;
		}
	}

	// Calculate success rate
	let successRate = $derived(() => {
		if (!stats) return 0;
		const total = stats.jobs_executed + stats.jobs_failed;
		return total > 0 ? (stats.jobs_executed / total) * 100 : 0;
	});

	// Get recent reports (last 5)
	let recentReports = $derived(() => {
		return reports.slice(0, 5);
	});
</script>

<div class="space-y-6">
	{#if loading}
		<div class="flex items-center justify-center h-64">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
		</div>
	{:else if error}
		<Card.Root class="p-6 bg-red-900/20 border-red-500/50">
			<Card.Header>
				<div class="flex items-center space-x-2">
					<AlertCircle class="w-5 h-5 text-red-400" />
					<h3 class="text-lg font-medium text-red-400">Error Loading Dashboard</h3>
				</div>
			</Card.Header>
			<Card.Description>
				<p class="mt-2 text-red-300">{error}</p>
			</Card.Description>
		</Card.Root>
	{:else}
		<!-- Stats Grid -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
			<Card.Root class="p-6">
				<Card.Header>
					<div class="flex items-center space-x-2">
						<TrendingUp class="w-5 h-5" />
						<h3 class="text-lg font-medium">Jobs Executed</h3>
					</div>
				</Card.Header>
				<Card.Description>
					<p class="mt-2 text-blue-300">{stats?.jobs_executed || 0}%</p>
				</Card.Description>
			</Card.Root>

			<Card.Root class="p-6">
				<Card.Header>
					<div class="flex items-center space-x-2">
						<Users class="w-5 h-5" />
						<h3 class="text-lg font-medium">Active Users</h3>
					</div>
				</Card.Header>
				<Card.Description>
					<p class="mt-2 text-green-300">{successRate().toFixed(1)}</p>
				</Card.Description>
			</Card.Root>
		</div>
	{/if}
</div>
