<!-- New Job Configuration Page -->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { apiClient, type JobConfig } from '$lib/api';
	import Button from '$lib/components/ui/button.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Label from '$lib/components/ui/label.svelte';
	import { ArrowLeft, Save } from 'lucide-svelte';
	import JobConfigForm from '../JobConfigForm.svelte';

	let loading = $state(false);
	let error = $state('');
	let success = $state(false);

	// Default job configuration
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

	async function saveJob() {
		// Debug logging
		console.log('Job ID value:', jobSchedule.job_id);
		console.log('Job ID length:', jobSchedule.job_id.length);
		console.log('Job ID trimmed:', jobSchedule.job_id.trim());
		console.log('Job ID trimmed length:', jobSchedule.job_id.trim().length);
		
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

		loading = true;
		error = '';

		try {
			const config = {
				...jobConfig,
				job_id: jobSchedule.job_id
			};

			if (jobSchedule.jobType === 'cron') {
				await apiClient.createCronJob({
					job_id: jobSchedule.job_id,
					hour: jobSchedule.hour,
					minute: jobSchedule.minute,
					day_of_week: jobSchedule.day_of_week,
					cron_expression: jobSchedule.cron_expression || undefined,
					config
				});
			} else if (jobSchedule.jobType === 'interval') {
				await apiClient.createIntervalJob({
					job_id: jobSchedule.job_id,
					minutes: jobSchedule.minutes,
					hours: jobSchedule.hours,
					days: jobSchedule.days,
					config
				});
			} else if (jobSchedule.jobType === 'onetime') {
				if (!jobSchedule.run_date) {
					error = 'Run date is required for one-time jobs';
					return;
				}

				const runDate = new Date(jobSchedule.run_date).toISOString();
				await apiClient.createOneTimeJob({
					job_id: jobSchedule.job_id,
					run_date: runDate,
					config
				});
			}

			success = true;
			// Redirect to jobs list after a short delay
			setTimeout(() => {
				goto('/jobs');
			}, 1500);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create job';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>New Job Configuration - Let's Talk</title>
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
				<h1 class="text-2xl font-bold text-white">Create New Job</h1>
				<p class="text-slate-400 mt-1">Configure a new pipeline job with comprehensive settings</p>
			</div>
		</div>
		<Button
			onclick={saveJob}
			disabled={loading}
			class="bg-blue-600 hover:bg-blue-700"
		>
			{#if loading}
				<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
				Creating...
			{:else}
				<Save class="w-4 h-4 mr-2" />
				Save Job
			{/if}
		</Button>
	</div>

	<!-- Success Message -->
	{#if success}
		<Card class="p-6 bg-green-900/20 border-green-500/50">
			<div class="flex items-center space-x-2">
				<div class="w-2 h-2 bg-green-400 rounded-full"></div>
				<h3 class="text-lg font-medium text-green-400">Job Created Successfully!</h3>
			</div>
			<p class="mt-2 text-green-300">Redirecting to jobs list...</p>
		</Card>
	{/if}

	<!-- Error Message -->
	{#if error}
		<Card class="p-6 bg-red-900/20 border-red-500/50">
			<div class="flex items-center space-x-2">
				<div class="w-2 h-2 bg-red-400 rounded-full"></div>
				<h3 class="text-lg font-medium text-red-400">Error</h3>
			</div>
			<p class="mt-2 text-red-300">{error}</p>
		</Card>
	{/if}

	<!-- Job Configuration Form -->
	<JobConfigForm 
		bind:jobConfig={jobConfig}
		bind:jobSchedule={jobSchedule}
		mode="create"
		disabled={loading}
	/>

	<!-- Debug Info -->
	{#if error || success}
		<Card class="p-6 bg-slate-900/20 border-slate-700">
			<div class="text-sm text-slate-300">
				<p><strong>Debug Info:</strong></p>
				<p>Job ID: "{jobSchedule.job_id}" (length: {jobSchedule.job_id.length})</p>
				<p>Collection Name: "{jobConfig.collection_name}"</p>
				<p>Embedding Model: "{jobConfig.embedding_model}"</p>
			</div>
		</Card>
	{/if}
</div>