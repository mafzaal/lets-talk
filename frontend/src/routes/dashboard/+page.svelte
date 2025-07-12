<script lang="ts">
	import { onMount } from 'svelte';
	import { apiClient, type SchedulerStats, type PipelineReport } from '$lib/api';
	import Card from '$lib/components/ui/card.svelte';
	import { Activity, AlertCircle, CheckCircle, Clock, TrendingUp, Users, Play } from 'lucide-svelte';

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
			case 'success': return 'text-green-400';
			case 'failed': return 'text-red-400';
			case 'running': return 'text-blue-400';
			default: return 'text-slate-400';
		}
	}

	function getStatusIcon(status: string) {
		switch (status?.toLowerCase()) {
			case 'success': return CheckCircle;
			case 'failed': return AlertCircle;
			case 'running': return Play;
			default: return Clock;
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
		<Card class="p-6 bg-red-900/20 border-red-500/50">
			<div class="flex items-center space-x-2">
				<AlertCircle class="w-5 h-5 text-red-400" />
				<h3 class="text-lg font-medium text-red-400">Error Loading Dashboard</h3>
			</div>
			<p class="mt-2 text-red-300">{error}</p>
		</Card>
	{:else}
		<!-- Stats Grid -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
			<!-- Total Jobs Executed -->
			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Jobs Executed</p>
						<p class="text-2xl font-bold text-white">{stats?.jobs_executed || 0}</p>
					</div>
					<div class="h-12 w-12 bg-green-500/10 rounded-lg flex items-center justify-center">
						<CheckCircle class="w-6 h-6 text-green-400" />
					</div>
				</div>
				<div class="mt-4 flex items-center">
					<TrendingUp class="w-4 h-4 text-green-400 mr-1" />
					<span class="text-sm text-slate-400">Success Rate: {successRate().toFixed(1)}%</span>
				</div>
			</Card>

			<!-- Failed Jobs -->
			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Failed Jobs</p>
						<p class="text-2xl font-bold text-white">{stats?.jobs_failed || 0}</p>
					</div>
					<div class="h-12 w-12 bg-red-500/10 rounded-lg flex items-center justify-center">
						<AlertCircle class="w-6 h-6 text-red-400" />
					</div>
				</div>
				<div class="mt-4 flex items-center">
					<span class="text-sm text-slate-400">
						{stats?.last_error ? 'Last error recorded' : 'No recent errors'}
					</span>
				</div>
			</Card>

			<!-- Active Jobs -->
			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Active Jobs</p>
						<p class="text-2xl font-bold text-white">{stats?.active_jobs || 0}</p>
					</div>
					<div class="h-12 w-12 bg-blue-500/10 rounded-lg flex items-center justify-center">
						<Activity class="w-6 h-6 text-blue-400" />
					</div>
				</div>
				<div class="mt-4 flex items-center">
					<div class="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
					<span class="text-sm text-slate-400">Scheduler running</span>
				</div>
			</Card>

			<!-- Last Execution -->
			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Last Execution</p>
						<p class="text-lg font-bold text-white">{formatDateTime(stats?.last_execution)}</p>
					</div>
					<div class="h-12 w-12 bg-purple-500/10 rounded-lg flex items-center justify-center">
						<Clock class="w-6 h-6 text-purple-400" />
					</div>
				</div>
				<div class="mt-4 flex items-center">
					<span class="text-sm text-slate-400">Next job scheduled</span>
				</div>
			</Card>
		</div>

		<!-- Execution History -->
		<Card class="bg-slate-900/50 border-slate-800">
			<div class="p-6 border-b border-slate-800">
				<h3 class="text-lg font-medium text-white">Recent Execution History</h3>
				<p class="text-sm text-slate-400 mt-1">Latest pipeline executions and their status</p>
			</div>
			<div class="p-6">
				{#if recentReports().length > 0}
					<div class="space-y-4">
						{#each recentReports() as report}
							{@const StatusIcon = getStatusIcon(report.status)}
							<div class="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
								<div class="flex items-center space-x-3">
									<div class="h-10 w-10 bg-slate-700 rounded-lg flex items-center justify-center">
										<StatusIcon class="w-5 h-5 {getStatusColor(report.status)}" />
									</div>
									<div>
										<h4 class="font-medium text-white">{report.job_id}</h4>
										<p class="text-sm text-slate-400">{formatDateTime(report.execution_time)}</p>
									</div>
								</div>
								<div class="flex items-center space-x-6">
									<div class="text-right">
										<p class="text-sm font-medium text-white">{report.total_documents} documents</p>
										<p class="text-xs text-slate-400">{report.duration}s duration</p>
									</div>
									<div class="flex items-center space-x-2">
										<span class="px-2 py-1 text-xs font-medium rounded-full {report.status === 'success' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}">
											{report.status}
										</span>
									</div>
								</div>
							</div>
						{/each}
					</div>
				{:else}
					<div class="text-center py-8">
						<Activity class="w-12 h-12 text-slate-600 mx-auto mb-4" />
						<p class="text-slate-400">No execution history available</p>
					</div>
				{/if}
			</div>
		</Card>

		<!-- System Status -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
			<Card class="bg-slate-900/50 border-slate-800">
				<div class="p-6">
					<h3 class="text-lg font-medium text-white mb-4">System Status</h3>
					<div class="space-y-3">
						<div class="flex items-center justify-between">
							<span class="text-slate-400">Scheduler Status</span>
							<div class="flex items-center space-x-2">
								<div class="w-2 h-2 bg-green-500 rounded-full"></div>
								<span class="text-green-400">Running</span>
							</div>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-slate-400">API Status</span>
							<div class="flex items-center space-x-2">
								<div class="w-2 h-2 bg-green-500 rounded-full"></div>
								<span class="text-green-400">Online</span>
							</div>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-slate-400">Database Status</span>
							<div class="flex items-center space-x-2">
								<div class="w-2 h-2 bg-green-500 rounded-full"></div>
								<span class="text-green-400">Connected</span>
							</div>
						</div>
					</div>
				</div>
			</Card>

			<Card class="bg-slate-900/50 border-slate-800">
				<div class="p-6">
					<h3 class="text-lg font-medium text-white mb-4">Quick Actions</h3>
					<div class="space-y-3">
						<button class="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
							<Play class="w-4 h-4" />
							<span>Run Pipeline Now</span>
						</button>
						<button class="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors">
							<Users class="w-4 h-4" />
							<span>View All Jobs</span>
						</button>
						<button class="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors">
							<Activity class="w-4 h-4" />
							<span>View Analytics</span>
						</button>
					</div>
				</div>
			</Card>
		</div>
	{/if}
</div>