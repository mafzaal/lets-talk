<script lang="ts">
	import { onMount } from 'svelte';
	import { apiClient, type JobResponse, type PipelineReport } from '$lib/api';
	import Card from '$lib/components/ui/card.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import { 
		Play, 
		Pause, 
		Plus, 
		Edit, 
		Trash2, 
		Clock, 
		Calendar, 
		AlertCircle,
		CheckCircle,
		Activity,
		Settings
	} from 'lucide-svelte';

	let jobs: JobResponse[] = $state([]);
	let reports: PipelineReport[] = $state([]);
	let loading = $state(true);
	let error = $state('');
	let showNewJobModal = $state(false);
	let runningJobs = $state(new Set<string>());

	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		try {
			const [jobsData, reportsData] = await Promise.all([
				apiClient.getJobs(),
				apiClient.getPipelineReports()
			]);
			
			jobs = jobsData;
			reports = reportsData.reports;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load jobs data';
		} finally {
			loading = false;
		}
	}

	async function runPipeline(jobId: string) {
		try {
			runningJobs.add(jobId);
			await apiClient.runPipeline();
			// Refresh data after running
			await loadData();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to run pipeline';
		} finally {
			runningJobs.delete(jobId);
		}
	}

	async function deleteJob(jobId: string) {
		if (!confirm('Are you sure you want to delete this job?')) return;
		
		try {
			await apiClient.deleteJob(jobId);
			await loadData();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to delete job';
		}
	}

	function formatDateTime(dateString: string | undefined) {
		if (!dateString) return 'Never';
		return new Date(dateString).toLocaleString();
	}

	function getJobExecutionHistory(jobId: string) {
		return reports.filter(report => report.job_id === jobId).slice(0, 3);
	}

	function getLastExecutionStatus(jobId: string) {
		const history = getJobExecutionHistory(jobId);
		return history.length > 0 ? history[0].status : 'never';
	}

	function getStatusColor(status: string) {
		switch (status?.toLowerCase()) {
			case 'success': return 'text-green-400';
			case 'failed': return 'text-red-400';
			case 'running': return 'text-blue-400';
			case 'never': return 'text-slate-400';
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

	function getTriggerTypeColor(trigger: string) {
		switch (trigger?.toLowerCase()) {
			case 'cron': return 'bg-blue-500/10 text-blue-400';
			case 'interval': return 'bg-purple-500/10 text-purple-400';
			case 'date': return 'bg-green-500/10 text-green-400';
			default: return 'bg-slate-500/10 text-slate-400';
		}
	}

	function renderStatusIcon(status: string) {
		const Icon = getStatusIcon(status);
		return Icon;
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
				<h3 class="text-lg font-medium text-red-400">Error Loading Jobs</h3>
			</div>
			<p class="mt-2 text-red-300">{error}</p>
		</Card>
	{:else}
		<!-- Header -->
		<div class="flex items-center justify-between">
			<div>
				<h2 class="text-2xl font-bold text-white">Pipeline Jobs</h2>
				<p class="text-slate-400 mt-1">Manage your scheduled and on-demand pipeline jobs</p>
			</div>
			<Button 
				class="bg-blue-600 hover:bg-blue-700" 
				onclick={() => showNewJobModal = true}
			>
				<Plus class="w-4 h-4 mr-2" />
				New Job
			</Button>
		</div>

		<!-- Jobs Overview -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Total Jobs</p>
						<p class="text-2xl font-bold text-white">{jobs.length}</p>
					</div>
					<div class="h-12 w-12 bg-blue-500/10 rounded-lg flex items-center justify-center">
						<Settings class="w-6 h-6 text-blue-400" />
					</div>
				</div>
			</Card>

			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Active Jobs</p>
						<p class="text-2xl font-bold text-white">{jobs.filter(j => j.next_run_time).length}</p>
					</div>
					<div class="h-12 w-12 bg-green-500/10 rounded-lg flex items-center justify-center">
						<Activity class="w-6 h-6 text-green-400" />
					</div>
				</div>
			</Card>

			<Card class="p-6 bg-slate-900/50 border-slate-800">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-slate-400">Recent Executions</p>
						<p class="text-2xl font-bold text-white">{reports.length}</p>
					</div>
					<div class="h-12 w-12 bg-purple-500/10 rounded-lg flex items-center justify-center">
						<Clock class="w-6 h-6 text-purple-400" />
					</div>
				</div>
			</Card>
		</div>

		<!-- Jobs List -->
		<Card class="bg-slate-900/50 border-slate-800">
			<div class="p-6 border-b border-slate-800">
				<h3 class="text-lg font-medium text-white">All Jobs</h3>
				<p class="text-sm text-slate-400 mt-1">View and manage your pipeline jobs</p>
			</div>
			<div class="p-6">
				{#if jobs.length > 0}
					<div class="space-y-4">
						{#each jobs as job}
							<div class="p-6 bg-slate-800/50 rounded-lg">
								<div class="flex items-start justify-between">
									<div class="flex-1">
										<div class="flex items-center space-x-3 mb-2">
											<h4 class="text-lg font-medium text-white">{job.name}</h4>
											<span class="px-2 py-1 text-xs font-medium rounded-full {getTriggerTypeColor(job.trigger)}">
												{job.trigger}
											</span>
											<span class="px-2 py-1 text-xs font-medium rounded-full {getStatusColor(getLastExecutionStatus(job.id))}">
												{getLastExecutionStatus(job.id)}
											</span>
										</div>
										<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
											<div>
												<p class="text-sm text-slate-400">Job ID</p>
												<p class="text-sm font-medium text-white">{job.id}</p>
											</div>
											<div>
												<p class="text-sm text-slate-400">Next Run</p>
												<p class="text-sm font-medium text-white">{formatDateTime(job.next_run_time)}</p>
											</div>
											<div>
												<p class="text-sm text-slate-400">Last Status</p>
												<div class="flex items-center space-x-2">
													{#if getLastExecutionStatus(job.id) === 'success'}
														<CheckCircle class="w-4 h-4 text-green-400" />
													{:else if getLastExecutionStatus(job.id) === 'failed'}
														<AlertCircle class="w-4 h-4 text-red-400" />
													{:else if getLastExecutionStatus(job.id) === 'running'}
														<Play class="w-4 h-4 text-blue-400" />
													{:else}
														<Clock class="w-4 h-4 text-slate-400" />
													{/if}
													<span class="text-sm font-medium text-white">{getLastExecutionStatus(job.id)}</span>
												</div>
											</div>
										</div>
									</div>
									<div class="flex items-center space-x-2 ml-4">
										<Button 
											variant="ghost" 
											size="sm"
											onclick={() => runPipeline(job.id)}
											disabled={runningJobs.has(job.id)}
										>
											{#if runningJobs.has(job.id)}
												<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
											{:else}
												<Play class="w-4 h-4" />
											{/if}
										</Button>
										<Button variant="ghost" size="sm">
											<Edit class="w-4 h-4" />
										</Button>
										<Button 
											variant="ghost" 
											size="sm"
											onclick={() => deleteJob(job.id)}
										>
											<Trash2 class="w-4 h-4" />
										</Button>
									</div>
								</div>

								<!-- Execution History -->
								{#if getJobExecutionHistory(job.id).length > 0}
									<div class="mt-4 pt-4 border-t border-slate-700">
										<h5 class="text-sm font-medium text-slate-400 mb-2">Recent Executions</h5>
										<div class="space-y-2">
											{#each getJobExecutionHistory(job.id) as execution}
												<div class="flex items-center justify-between text-sm">
													<div class="flex items-center space-x-2">
														{#if execution.status === 'success'}
															<CheckCircle class="w-4 h-4 text-green-400" />
														{:else if execution.status === 'failed'}
															<AlertCircle class="w-4 h-4 text-red-400" />
														{:else if execution.status === 'running'}
															<Play class="w-4 h-4 text-blue-400" />
														{:else}
															<Clock class="w-4 h-4 text-slate-400" />
														{/if}
														<span class="text-slate-300">{formatDateTime(execution.execution_time)}</span>
													</div>
													<div class="flex items-center space-x-4">
														<span class="text-slate-400">{execution.total_documents} docs</span>
														<span class="text-slate-400">{execution.duration}s</span>
														<span class="px-2 py-1 text-xs rounded-full {execution.status === 'success' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}">
															{execution.status}
														</span>
													</div>
												</div>
											{/each}
										</div>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{:else}
					<div class="text-center py-12">
						<Settings class="w-16 h-16 text-slate-600 mx-auto mb-4" />
						<h3 class="text-lg font-medium text-slate-400 mb-2">No jobs configured</h3>
						<p class="text-slate-500 mb-4">Get started by creating your first pipeline job</p>
						<Button 
							class="bg-blue-600 hover:bg-blue-700" 
							onclick={() => showNewJobModal = true}
						>
							<Plus class="w-4 h-4 mr-2" />
							Create Job
						</Button>
					</div>
				{/if}
			</div>
		</Card>
	{/if}
</div>

<!-- New Job Modal -->
{#if showNewJobModal}
	<div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
		<Card class="w-full max-w-md bg-slate-900 border-slate-800">
			<div class="p-6">
				<h3 class="text-lg font-medium text-white mb-4">Create New Job</h3>
				<div class="space-y-4">
					<div>
						<label for="jobName" class="block text-sm font-medium text-slate-400 mb-1">Job Name</label>
						<input 
							id="jobName"
							type="text" 
							class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
							placeholder="Enter job name"
						>
					</div>
					<div>
						<label for="jobType" class="block text-sm font-medium text-slate-400 mb-1">Job Type</label>
						<select id="jobType" class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
							<option value="cron">Cron Schedule</option>
							<option value="interval">Interval</option>
							<option value="oneTime">One Time</option>
						</select>
					</div>
					<div>
						<label for="schedule" class="block text-sm font-medium text-slate-400 mb-1">Schedule</label>
						<input 
							id="schedule"
							type="text" 
							class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
							placeholder="0 0 * * *"
						>
					</div>
				</div>
				<div class="flex justify-end space-x-3 mt-6">
					<Button 
						variant="ghost" 
						onclick={() => showNewJobModal = false}
					>
						Cancel
					</Button>
					<Button class="bg-blue-600 hover:bg-blue-700">
						Create Job
					</Button>
				</div>
			</div>
		</Card>
	</div>
{/if}