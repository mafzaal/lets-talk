<script lang="ts">
	import { onMount } from 'svelte';
	import { apiClient, type PipelineReport } from '$lib/api';
	import Card from '$lib/components/ui/card.svelte';
	import { Activity, CheckCircle, AlertCircle, Clock, Play, User, Settings } from 'lucide-svelte';

	let reports: PipelineReport[] = $state([]);
	let loading = $state(true);
	let error = $state('');

	// Mock activity data for demonstration
	let activityFeed = [
		{
			id: 1,
			type: 'job_created',
			title: 'New job created',
			description: 'Daily blog update job created by admin',
			timestamp: '2024-01-15T10:30:00Z',
			user: 'admin',
			icon: Settings
		},
		{
			id: 2,
			type: 'job_executed',
			title: 'Job executed successfully',
			description: 'Daily blog update completed in 3.2s',
			timestamp: '2024-01-15T10:15:00Z',
			user: 'system',
			icon: CheckCircle
		},
		{
			id: 3,
			type: 'job_failed',
			title: 'Job execution failed',
			description: 'Weekly summary job failed due to timeout',
			timestamp: '2024-01-15T09:45:00Z',
			user: 'system',
			icon: AlertCircle
		},
		{
			id: 4,
			type: 'job_started',
			title: 'Job started',
			description: 'Content indexing job started',
			timestamp: '2024-01-15T09:30:00Z',
			user: 'system',
			icon: Play
		},
		{
			id: 5,
			type: 'user_login',
			title: 'User logged in',
			description: 'Admin user logged into the system',
			timestamp: '2024-01-15T09:00:00Z',
			user: 'admin',
			icon: User
		},
		{
			id: 6,
			type: 'job_executed',
			title: 'Job executed successfully',
			description: 'Hourly sync completed in 1.8s',
			timestamp: '2024-01-15T08:00:00Z',
			user: 'system',
			icon: CheckCircle
		},
	];

	onMount(async () => {
		try {
			const reportsData = await apiClient.getPipelineReports();
			reports = reportsData.reports;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load activity data';
		} finally {
			loading = false;
		}
	});

	function formatDateTime(dateString: string) {
		return new Date(dateString).toLocaleString();
	}

	function getRelativeTime(dateString: string) {
		const now = new Date();
		const date = new Date(dateString);
		const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
		
		if (diffInSeconds < 60) return 'Just now';
		if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
		if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
		return `${Math.floor(diffInSeconds / 86400)}d ago`;
	}

	function getActivityTypeColor(type: string) {
		switch (type) {
			case 'job_created': return 'bg-blue-500/10 text-blue-400';
			case 'job_executed': return 'bg-green-500/10 text-green-400';
			case 'job_failed': return 'bg-red-500/10 text-red-400';
			case 'job_started': return 'bg-purple-500/10 text-purple-400';
			case 'user_login': return 'bg-orange-500/10 text-orange-400';
			default: return 'bg-slate-500/10 text-slate-400';
		}
	}
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
				<h3 class="text-lg font-medium text-red-400">Error Loading Activity</h3>
			</div>
			<p class="mt-2 text-red-300">{error}</p>
		</Card>
	{:else}
		<!-- Header -->
		<div>
			<h2 class="text-2xl font-bold text-white">Activity Feed</h2>
			<p class="text-slate-400 mt-1">Track all system activities and user interactions</p>
		</div>

		<!-- Activity Stats -->
		<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Total Activities</p>
						<p class="text-2xl font-bold text-white">{activityFeed.length}</p>
					</div>
					<div class="h-12 w-12 bg-blue-500/10 rounded-lg flex items-center justify-center">
						<Activity class="w-6 h-6 text-blue-400" />
					</div>
				</div>
			</Card>

			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Jobs Today</p>
						<p class="text-2xl font-bold text-white">{activityFeed.filter(a => a.type.includes('job')).length}</p>
					</div>
					<div class="h-12 w-12 bg-green-500/10 rounded-lg flex items-center justify-center">
						<Settings class="w-6 h-6 text-green-400" />
					</div>
				</div>
			</Card>

			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Success Rate</p>
						<p class="text-2xl font-bold text-white">94%</p>
					</div>
					<div class="h-12 w-12 bg-green-500/10 rounded-lg flex items-center justify-center">
						<CheckCircle class="w-6 h-6 text-green-400" />
					</div>
				</div>
			</Card>

			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Active Users</p>
						<p class="text-2xl font-bold text-white">3</p>
					</div>
					<div class="h-12 w-12 bg-purple-500/10 rounded-lg flex items-center justify-center">
						<User class="w-6 h-6 text-purple-400" />
					</div>
				</div>
			</Card>
		</div>

		<!-- Activity Feed -->
		<Card class="bg-slate-900/50 border-slate-800">
			<div class="p-6 border-b border-slate-800">
				<h3 class="text-lg font-medium text-white">Recent Activity</h3>
				<p class="text-sm text-slate-400 mt-1">Latest system events and user actions</p>
			</div>
			<div class="p-6">
				<div class="space-y-4">
					{#each activityFeed as activity}
						<div class="flex items-start space-x-4">
							<div class="h-10 w-10 rounded-lg flex items-center justify-center {getActivityTypeColor(activity.type)}">
								<activity.icon class="w-5 h-5" />
							</div>
							<div class="flex-1">
								<div class="flex items-center justify-between">
									<h4 class="font-medium text-white">{activity.title}</h4>
									<span class="text-sm text-slate-400">{getRelativeTime(activity.timestamp)}</span>
								</div>
								<p class="text-sm text-slate-400 mt-1">{activity.description}</p>
								<div class="flex items-center space-x-2 mt-2">
									<span class="text-xs text-slate-500">by {activity.user}</span>
									<span class="text-xs text-slate-500">•</span>
									<span class="text-xs text-slate-500">{formatDateTime(activity.timestamp)}</span>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</Card>

		<!-- Recent Pipeline Reports -->
		{#if reports.length > 0}
			<Card class="bg-slate-900/50 border-slate-800">
				<div class="p-6 border-b border-slate-800">
					<h3 class="text-lg font-medium text-white">Pipeline Execution History</h3>
					<p class="text-sm text-slate-400 mt-1">Recent pipeline execution results from API</p>
				</div>
				<div class="p-6">
					<div class="space-y-4">
						{#each reports.slice(0, 5) as report}
							<div class="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
								<div class="flex items-center space-x-3">
									<div class="h-10 w-10 bg-slate-700 rounded-lg flex items-center justify-center">
										{#if report.status === 'success'}
											<CheckCircle class="w-5 h-5 text-green-400" />
										{:else if report.status === 'failed'}
											<AlertCircle class="w-5 h-5 text-red-400" />
										{:else}
											<Clock class="w-5 h-5 text-slate-400" />
										{/if}
									</div>
									<div>
										<h4 class="font-medium text-white">{report.job_id}</h4>
										<p class="text-sm text-slate-400">{formatDateTime(report.execution_time)}</p>
									</div>
								</div>
								<div class="text-right">
									<p class="text-sm font-medium text-white">{report.total_documents} documents</p>
									<p class="text-xs text-slate-400">{report.duration}s duration</p>
								</div>
							</div>
						{/each}
					</div>
				</div>
			</Card>
		{/if}
	{/if}
</div>