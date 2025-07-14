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
		Settings,
		X
	} from 'lucide-svelte';
	import {
		Dialog,
		DialogContent,
		DialogHeader,
		DialogTitle,
		DialogFooter,
		DialogDescription
	} from '$lib/components/ui/dialog';
	import Input from '$lib/components/ui/input.svelte';
	import Label from '$lib/components/ui/label.svelte';

	let jobs: JobResponse[] = $state([]);
	let reports: PipelineReport[] = $state([]);
	let loading = $state(true);
	let error = $state('');
	let showNewJobModal = $state(false);
	let runningJobs = $state(new Set<string>());
	let creatingJob = $state(false);

	// Job creation form state
	let jobForm = $state({
		job_id: '',
		jobType: 'cron' as 'cron' | 'interval' | 'onetime',
		// Cron fields
		hour: undefined as number | undefined,
		minute: 0,
		day_of_week: undefined as string | undefined,
		cron_expression: '',
		// Interval fields
		minutes: undefined as number | undefined,
		hours: undefined as number | undefined,
		days: undefined as number | undefined,
		// One-time fields
		run_date: ''
	});

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

	async function createJob() {
		// Debug: log the form values using snapshot
		console.log('Creating job with form data:', $state.snapshot(jobForm));
		
		if (!jobForm.job_id || !jobForm.job_id.trim()) {
			error = 'Job ID is required';
			return;
		}

		creatingJob = true;
		error = '';

		try {
			if (jobForm.jobType === 'cron') {
				await apiClient.createCronJob({
					job_id: jobForm.job_id,
					hour: jobForm.hour,
					minute: jobForm.minute,
					day_of_week: jobForm.day_of_week || undefined,
					cron_expression: jobForm.cron_expression || undefined
				});
			} else if (jobForm.jobType === 'interval') {
				await apiClient.createIntervalJob({
					job_id: jobForm.job_id,
					minutes: jobForm.minutes,
					hours: jobForm.hours,
					days: jobForm.days
				});
			} else if (jobForm.jobType === 'onetime') {
				if (!jobForm.run_date) {
					error = 'Run date is required for one-time jobs';
					return;
				}
				
				// Convert to ISO format for API
				const runDate = new Date(jobForm.run_date).toISOString();
				
				await apiClient.createOneTimeJob({
					job_id: jobForm.job_id,
					run_date: runDate
				});
			}

			// Reset form and close modal
			resetJobForm();
			showNewJobModal = false;
			await loadData();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create job';
		} finally {
			creatingJob = false;
		}
	}

	function resetJobForm() {
		jobForm = {
			job_id: '',
			jobType: 'cron',
			hour: undefined,
			minute: 0,
			day_of_week: undefined,
			cron_expression: '',
			minutes: undefined,
			hours: undefined,
			days: undefined,
			run_date: ''
		};
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
				onclick={() => {
					error = '';
					showNewJobModal = true;
				}}
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
							onclick={() => {
								error = '';
								showNewJobModal = true;
							}}
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
<Dialog bind:open={showNewJobModal}>
	<DialogContent class="max-w-2xl bg-slate-900 border-slate-800">
		<DialogHeader>
			<DialogTitle class="text-white">Create New Job</DialogTitle>
			<DialogDescription class="text-slate-400">
				Create a new scheduled job for your pipeline processing.
			</DialogDescription>
		</DialogHeader>
		
		<div class="space-y-6">
			{#if error}
				<div class="p-4 bg-red-900/20 border border-red-500/50 rounded-md">
					<div class="flex items-center space-x-2">
						<AlertCircle class="w-5 h-5 text-red-400" />
						<span class="text-red-400 font-medium">Error</span>
					</div>
					<p class="text-red-300 mt-1">{error}</p>
				</div>
			{/if}

			<div class="space-y-4">
				<!-- Job ID -->
				<div class="space-y-2">
					<Label for="jobId" class="text-slate-300">Job ID</Label>
					<Input 
						id="jobId"
						bind:value={jobForm.job_id}
						placeholder="Enter unique job identifier"
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						oninput={(e) => {
							jobForm.job_id = e.target.value;
						}}
					/>
				</div>

				<!-- Job Type -->
				<div class="space-y-2">
					<Label for="jobType" class="text-slate-300">Job Type</Label>
					<select 
						id="jobType"
						bind:value={jobForm.jobType}
						class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
					>
						<option value="cron">Cron Schedule</option>
						<option value="interval">Interval</option>
						<option value="onetime">One Time</option>
					</select>
				</div>

				<!-- Cron Fields -->
				{#if jobForm.jobType === 'cron'}
					<div class="space-y-4 p-4 bg-slate-800/50 rounded-md">
						<h4 class="text-slate-300 font-medium">Cron Schedule Configuration</h4>
						
						<div class="space-y-2">
							<Label for="cronExpression" class="text-slate-300">Cron Expression (optional)</Label>
							<Input 
								id="cronExpression"
								bind:value={jobForm.cron_expression}
								placeholder="0 0 * * * (leave empty to use hour/minute/day fields)"
								class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
								oninput={(e) => {
									jobForm.cron_expression = e.target.value;
								}}
							/>
						</div>

						<div class="grid grid-cols-3 gap-4">
							<div class="space-y-2">
								<Label for="hour" class="text-slate-300">Hour (0-23)</Label>
								<Input 
									id="hour"
									type="number"
									min="0"
									max="23"
									bind:value={jobForm.hour}
									placeholder="0"
									class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
									oninput={(e) => {
										jobForm.hour = e.target.value ? parseInt(e.target.value) : undefined;
									}}
								/>
							</div>
							<div class="space-y-2">
								<Label for="minute" class="text-slate-300">Minute (0-59)</Label>
								<Input 
									id="minute"
									type="number"
									min="0"
									max="59"
									bind:value={jobForm.minute}
									placeholder="0"
									class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
									oninput={(e) => {
										jobForm.minute = e.target.value ? parseInt(e.target.value) : 0;
									}}
								/>
							</div>
							<div class="space-y-2">
								<Label for="dayOfWeek" class="text-slate-300">Day of Week</Label>
								<select 
									id="dayOfWeek"
									bind:value={jobForm.day_of_week}
									class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
								>
									<option value="">Every day</option>
									<option value="mon">Monday</option>
									<option value="tue">Tuesday</option>
									<option value="wed">Wednesday</option>
									<option value="thu">Thursday</option>
									<option value="fri">Friday</option>
									<option value="sat">Saturday</option>
									<option value="sun">Sunday</option>
								</select>
							</div>
						</div>
					</div>
				{/if}

				<!-- Interval Fields -->
				{#if jobForm.jobType === 'interval'}
					<div class="space-y-4 p-4 bg-slate-800/50 rounded-md">
						<h4 class="text-slate-300 font-medium">Interval Configuration</h4>
						
						<div class="grid grid-cols-3 gap-4">
							<div class="space-y-2">
								<Label for="minutes" class="text-slate-300">Minutes</Label>
								<Input 
									id="minutes"
									type="number"
									min="0"
									bind:value={jobForm.minutes}
									placeholder="0"
									class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
									oninput={(e) => {
										jobForm.minutes = e.target.value ? parseInt(e.target.value) : undefined;
									}}
								/>
							</div>
							<div class="space-y-2">
								<Label for="hours" class="text-slate-300">Hours</Label>
								<Input 
									id="hours"
									type="number"
									min="0"
									bind:value={jobForm.hours}
									placeholder="0"
									class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
									oninput={(e) => {
										jobForm.hours = e.target.value ? parseInt(e.target.value) : undefined;
									}}
								/>
							</div>
							<div class="space-y-2">
								<Label for="days" class="text-slate-300">Days</Label>
								<Input 
									id="days"
									type="number"
									min="0"
									bind:value={jobForm.days}
									placeholder="0"
									class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
									oninput={(e) => {
										jobForm.days = e.target.value ? parseInt(e.target.value) : undefined;
									}}
								/>
							</div>
						</div>
						<p class="text-sm text-slate-400">Specify at least one time unit (minutes, hours, or days)</p>
					</div>
				{/if}

				<!-- One Time Fields -->
				{#if jobForm.jobType === 'onetime'}
					<div class="space-y-4 p-4 bg-slate-800/50 rounded-md">
						<h4 class="text-slate-300 font-medium">One-Time Schedule</h4>
						
						<div class="space-y-2">
							<Label for="runDate" class="text-slate-300">Run Date & Time</Label>
							<Input 
								id="runDate"
								type="datetime-local"
								bind:value={jobForm.run_date}
								class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
								oninput={(e) => {
									jobForm.run_date = e.target.value;
								}}
							/>
						</div>
					</div>
				{/if}
			</div>
		</div>

		<DialogFooter>
			<Button 
				variant="ghost" 
				onclick={() => {
					showNewJobModal = false;
					resetJobForm();
					error = '';
				}}
				disabled={creatingJob}
			>
				Cancel
			</Button>
			<Button 
				class="bg-blue-600 hover:bg-blue-700" 
				onclick={createJob}
				disabled={creatingJob}
			>
				{#if creatingJob}
					<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
					Creating...
				{:else}
					Create Job
				{/if}
			</Button>
		</DialogFooter>
	</DialogContent>
</Dialog>