<!-- Edit Job Configuration Page -->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { apiClient, type JobConfig, type JobResponse } from '$lib/api';
	import Button from '$lib/components/ui/button.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import { ArrowLeft, Save, AlertCircle } from 'lucide-svelte';
	import JobConfigForm from '../../JobConfigForm.svelte';

	let loading = $state(true);
	let saving = $state(false);
	let error = $state('');
	let success = $state(false);
	let job = $state<JobResponse | null>(null);

	// Job configuration
	let jobConfig = $state<JobConfig>({
		data_dir: 'data/',
		data_dir_pattern: '*.md',
		web_urls: [],
		base_url: '',
		blog_base_url: '',
		index_only_published_posts: true,
		use_chunking: true,
		chunking_strategy: 'semantic',
		adaptive_chunking: true,
		chunk_size: 1000,
		chunk_overlap: 200,
		semantic_breakpoint_type: 'percentile',
		semantic_breakpoint_threshold_amount: 95.0,
		semantic_min_chunk_size: 100,
		collection_name: 'lets_talk_documents',
		embedding_model: 'ollama:snowflake-arctic-embed2:latest',
		force_recreate: false,
		incremental_mode: 'auto',
		checksum_algorithm: 'sha256',
		auto_detect_changes: true,
		incremental_fallback_threshold: 0.8,
		enable_batch_processing: true,
		batch_size: 50,
		enbable_performance_monitoring: true,
		batch_pause_seconds: 0.1,
		max_concurrent_operations: 5,
		max_backup_files: 3,
		metadata_csv: 'blog_metadata.csv',
		blog_stats_filename: 'blog_stats_latest.json',
		blog_docs_filename: 'blog_docs.csv',
		health_report_filename: 'health_report.json',
		ci_summary_filename: 'ci_summary.json',
		build_info_filename: 'vector_store_build_info.json'
	});

	// Job scheduling configuration
	let jobSchedule = $state({
		job_id: '',
		jobType: 'cron' as 'cron' | 'interval' | 'onetime',
		// Cron fields
		hour: 0,
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

	// Get job ID from URL
	let jobId = $derived($page.params.id);

	onMount(async () => {
		await loadJob();
	});

	async function loadJob() {
		try {
			loading = true;
			error = '';

			// Load job from API
			job = await apiClient.getJob(jobId);
			
			// Populate form with job data
			if (job) {
				jobSchedule.job_id = job.id;
				
				// Parse trigger type and schedule
				if (job.trigger.includes('cron')) {
					jobSchedule.jobType = 'cron';
					// Parse cron expression or time components
					// This is a simplified parsing - in production you'd want more robust parsing
					const cronMatch = job.trigger.match(/hour=(\d+).*minute=(\d+)/);
					if (cronMatch) {
						jobSchedule.hour = parseInt(cronMatch[1]);
						jobSchedule.minute = parseInt(cronMatch[2]);
					}
				} else if (job.trigger.includes('interval')) {
					jobSchedule.jobType = 'interval';
					// Parse interval components
					const minutesMatch = job.trigger.match(/minutes=(\d+)/);
					const hoursMatch = job.trigger.match(/hours=(\d+)/);
					const daysMatch = job.trigger.match(/days=(\d+)/);
					
					if (minutesMatch) jobSchedule.minutes = parseInt(minutesMatch[1]);
					if (hoursMatch) jobSchedule.hours = parseInt(hoursMatch[1]);
					if (daysMatch) jobSchedule.days = parseInt(daysMatch[1]);
				} else if (job.trigger.includes('date')) {
					jobSchedule.jobType = 'onetime';
					// Parse date
					const dateMatch = job.trigger.match(/run_date=(.+)/);
					if (dateMatch) {
						jobSchedule.run_date = dateMatch[1];
					}
				}

				// Load job configuration
				if (job.config) {
					jobConfig = {
						...jobConfig,
						...job.config
					};
				}
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load job';
		} finally {
			loading = false;
		}
	}

	async function saveJob() {
		if (!jobSchedule.job_id.trim()) {
			error = 'Job ID is required';
			return;
		}

		if (!jobConfig.collection_name.trim()) {
			error = 'Collection name is required';
			return;
		}

		if (!jobConfig.embedding_model.trim()) {
			error = 'Embedding model is required';
			return;
		}

		saving = true;
		error = '';

		try {
			const config = {
				...jobConfig,
				job_id: jobSchedule.job_id
			};

			await apiClient.updateJob(jobId, {
				job_id: jobSchedule.job_id,
				jobType: jobSchedule.jobType,
				hour: jobSchedule.hour,
				minute: jobSchedule.minute,
				day_of_week: jobSchedule.day_of_week || undefined,
				cron_expression: jobSchedule.cron_expression || undefined,
				minutes: jobSchedule.minutes,
				hours: jobSchedule.hours,
				days: jobSchedule.days,
				run_date: jobSchedule.run_date,
				config
			});

			success = true;
			// Redirect to jobs list after a short delay
			setTimeout(() => {
				goto('/jobs');
			}, 1500);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to update job';
		} finally {
			saving = false;
		}
	}
</script>

<svelte:head>
	<title>Edit Job Configuration - Let's Talk</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div class="flex items-center space-x-4">
			<Button
				variant="ghost"
				size="sm"
				onclick={() => goto('/jobs')}
				class="text-slate-400 hover:text-white"
			>
				<ArrowLeft class="w-4 h-4 mr-2" />
				Back to Jobs
			</Button>
			<div>
				<h1 class="text-2xl font-bold text-white">Edit Job Configuration</h1>
				<p class="text-slate-400 mt-1">
					{#if job}
						Editing job: {job.name}
					{:else}
						Loading job configuration...
					{/if}
				</p>
			</div>
		</div>
		<div class="flex items-center space-x-2">
			<Button
				variant="outline"
				onclick={() => goto('/jobs')}
				disabled={saving}
				class="border-slate-700 text-slate-300 hover:bg-slate-800"
			>
				Cancel
			</Button>
			<Button
				onclick={saveJob}
				disabled={saving || loading}
				class="bg-blue-600 hover:bg-blue-700"
			>
				{#if saving}
					<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
					Saving...
				{:else}
					<Save class="w-4 h-4 mr-2" />
					Save Changes
				{/if}
			</Button>
		</div>
	</div>

	<!-- Loading State -->
	{#if loading}
		<Card class="p-6 bg-slate-900/50 border-slate-800">
			<div class="flex items-center justify-center space-x-2">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
				<span class="text-slate-400">Loading job configuration...</span>
			</div>
		</Card>
	{/if}

	<!-- Success Message -->
	{#if success}
		<Card class="p-6 bg-green-900/20 border-green-500/50">
			<div class="flex items-center space-x-2">
				<div class="w-2 h-2 bg-green-400 rounded-full"></div>
				<h3 class="text-lg font-medium text-green-400">Job Updated Successfully!</h3>
			</div>
			<p class="mt-2 text-green-300">Redirecting to jobs list...</p>
		</Card>
	{/if}

	<!-- Error Message -->
	{#if error}
		<Card class="p-6 bg-red-900/20 border-red-500/50">
			<div class="flex items-center space-x-2">
				<AlertCircle class="w-5 h-5 text-red-400" />
				<h3 class="text-lg font-medium text-red-400">Error</h3>
			</div>
			<p class="mt-2 text-red-300">{error}</p>
		</Card>
	{/if}

	<!-- Job Configuration Form -->
	{#if !loading && job}
		<JobConfigForm 
			bind:jobConfig={jobConfig}
			bind:jobSchedule={jobSchedule}
			mode="edit"
			disabled={saving}
		/>
	{/if}
</div>