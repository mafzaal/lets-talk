<script lang="ts">
	import { onMount } from 'svelte';
	import { apiClient, type SchedulerStats } from '$lib/api';
	import Card from '$lib/components/ui/card.svelte';
	import { BarChart3, TrendingUp, TrendingDown, Activity, Users, Clock, AlertCircle } from 'lucide-svelte';

	let stats: SchedulerStats | null = $state(null);
	let loading = $state(true);
	let error = $state('');

	// Mock data for demonstration
	let performanceData = [
		{ period: 'Jan', executions: 45, success: 42, failed: 3 },
		{ period: 'Feb', executions: 52, success: 48, failed: 4 },
		{ period: 'Mar', executions: 38, success: 35, failed: 3 },
		{ period: 'Apr', executions: 61, success: 58, failed: 3 },
		{ period: 'May', executions: 49, success: 47, failed: 2 },
		{ period: 'Jun', executions: 55, success: 52, failed: 3 },
	];

	onMount(async () => {
		try {
			stats = await apiClient.getSchedulerStats();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load analytics data';
		} finally {
			loading = false;
		}
	});

	let successRate = $derived(() => {
		if (!stats) return 0;
		const total = stats.jobs_executed + stats.jobs_failed;
		return total > 0 ? (stats.jobs_executed / total) * 100 : 0;
	});

	let totalExecutions = $derived(() => {
		return performanceData.reduce((sum, item) => sum + item.executions, 0);
	});

	let averageSuccessRate = $derived(() => {
		const totalExecs = performanceData.reduce((sum, item) => sum + item.executions, 0);
		const totalSuccess = performanceData.reduce((sum, item) => sum + item.success, 0);
		return totalExecs > 0 ? (totalSuccess / totalExecs) * 100 : 0;
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
				<h3 class="text-lg font-medium text-red-400">Error Loading Analytics</h3>
			</div>
			<p class="mt-2 text-red-300">{error}</p>
		</Card>
	{:else}
		<!-- Header -->
		<div>
			<h2 class="text-2xl font-bold text-white">Analytics & Performance</h2>
			<p class="text-slate-400 mt-1">Monitor pipeline performance and system metrics</p>
		</div>

		<!-- Key Metrics -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Total Executions</p>
						<p class="text-2xl font-bold text-white">{totalExecutions}</p>
					</div>
					<div class="h-12 w-12 bg-blue-500/10 rounded-lg flex items-center justify-center">
						<Activity class="w-6 h-6 text-blue-400" />
					</div>
				</div>
				<div class="mt-4 flex items-center">
					<TrendingUp class="w-4 h-4 text-green-400 mr-1" />
					<span class="text-sm text-slate-400">+12% from last month</span>
				</div>
			</Card>

			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Success Rate</p>
						<p class="text-2xl font-bold text-white">{averageSuccessRate.toFixed(1)}%</p>
					</div>
					<div class="h-12 w-12 bg-green-500/10 rounded-lg flex items-center justify-center">
						<TrendingUp class="w-6 h-6 text-green-400" />
					</div>
				</div>
				<div class="mt-4 flex items-center">
					<TrendingUp class="w-4 h-4 text-green-400 mr-1" />
					<span class="text-sm text-slate-400">+2.3% improvement</span>
				</div>
			</Card>

			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Avg Duration</p>
						<p class="text-2xl font-bold text-white">4.2s</p>
					</div>
					<div class="h-12 w-12 bg-purple-500/10 rounded-lg flex items-center justify-center">
						<Clock class="w-6 h-6 text-purple-400" />
					</div>
				</div>
				<div class="mt-4 flex items-center">
					<TrendingDown class="w-4 h-4 text-green-400 mr-1" />
					<span class="text-sm text-slate-400">-0.8s faster</span>
				</div>
			</Card>

			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Active Users</p>
						<p class="text-2xl font-bold text-white">1,234</p>
					</div>
					<div class="h-12 w-12 bg-orange-500/10 rounded-lg flex items-center justify-center">
						<Users class="w-6 h-6 text-orange-400" />
					</div>
				</div>
				<div class="mt-4 flex items-center">
					<TrendingUp class="w-4 h-4 text-green-400 mr-1" />
					<span class="text-sm text-slate-400">+8.4% growth</span>
				</div>
			</Card>
		</div>

		<!-- Performance Chart -->
		<Card class="bg-slate-900/50 border-slate-800">
			<div class="p-6 border-b border-slate-800">
				<h3 class="text-lg font-medium text-white">Execution Performance</h3>
				<p class="text-sm text-slate-400 mt-1">Monthly pipeline execution trends</p>
			</div>
			<div class="p-6">
				<div class="h-64 flex items-end justify-between space-x-4">
					{#each performanceData as item}
						<div class="flex flex-col items-center flex-1">
							<div class="w-full bg-slate-800 rounded-t-lg overflow-hidden" style="height: {(item.executions / 70) * 200}px;">
								<div class="w-full bg-green-500 rounded-t-lg" style="height: {(item.success / item.executions) * 100}%;"></div>
							</div>
							<div class="mt-2 text-xs text-slate-400 text-center">
								<p class="font-medium">{item.period}</p>
								<p>{item.executions} exec</p>
							</div>
						</div>
					{/each}
				</div>
				<div class="mt-6 flex items-center justify-center space-x-6">
					<div class="flex items-center space-x-2">
						<div class="w-3 h-3 bg-green-500 rounded-full"></div>
						<span class="text-sm text-slate-400">Successful</span>
					</div>
					<div class="flex items-center space-x-2">
						<div class="w-3 h-3 bg-slate-700 rounded-full"></div>
						<span class="text-sm text-slate-400">Failed</span>
					</div>
				</div>
			</div>
		</Card>

		<!-- Performance Summary -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
			<Card class="bg-slate-900/50 border-slate-800">
				<div class="p-6">
					<h3 class="text-lg font-medium text-white mb-4">Performance Summary</h3>
					<div class="space-y-4">
						<div class="flex justify-between items-center">
							<span class="text-slate-400">Peak Performance</span>
							<span class="text-white font-medium">98.4% success rate</span>
						</div>
						<div class="flex justify-between items-center">
							<span class="text-slate-400">Fastest Execution</span>
							<span class="text-white font-medium">1.2s</span>
						</div>
						<div class="flex justify-between items-center">
							<span class="text-slate-400">Most Active Period</span>
							<span class="text-white font-medium">2-4 PM UTC</span>
						</div>
						<div class="flex justify-between items-center">
							<span class="text-slate-400">Error Rate</span>
							<span class="text-white font-medium">2.1%</span>
						</div>
					</div>
				</div>
			</Card>

			<Card class="bg-slate-900/50 border-slate-800">
				<div class="p-6">
					<h3 class="text-lg font-medium text-white mb-4">Resource Usage</h3>
					<div class="space-y-4">
						<div>
							<div class="flex justify-between items-center mb-2">
								<span class="text-slate-400">CPU Usage</span>
								<span class="text-white font-medium">34%</span>
							</div>
							<div class="w-full bg-slate-800 rounded-full h-2">
								<div class="bg-blue-500 h-2 rounded-full" style="width: 34%"></div>
							</div>
						</div>
						<div>
							<div class="flex justify-between items-center mb-2">
								<span class="text-slate-400">Memory Usage</span>
								<span class="text-white font-medium">67%</span>
							</div>
							<div class="w-full bg-slate-800 rounded-full h-2">
								<div class="bg-green-500 h-2 rounded-full" style="width: 67%"></div>
							</div>
						</div>
						<div>
							<div class="flex justify-between items-center mb-2">
								<span class="text-slate-400">Disk Usage</span>
								<span class="text-white font-medium">45%</span>
							</div>
							<div class="w-full bg-slate-800 rounded-full h-2">
								<div class="bg-purple-500 h-2 rounded-full" style="width: 45%"></div>
							</div>
						</div>
					</div>
				</div>
			</Card>
		</div>
	{/if}
</div>