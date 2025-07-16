<!-- Job Configuration Form Component -->
<script lang="ts">
	import { type JobConfig } from '$lib/api';
	import Card from '$lib/components/ui/card.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Label from '$lib/components/ui/label.svelte';
	import Switch from '$lib/components/ui/switch.svelte';
	import { Calendar, Clock, Settings, Database, FileText, Zap, Activity } from 'lucide-svelte';

	interface JobSchedule {
		job_id: string;
		jobType: 'cron' | 'interval' | 'onetime';
		hour: number;
		minute: number;
		day_of_week?: string;
		cron_expression: string;
		minutes?: number;
		hours?: number;
		days?: number;
		run_date: string;
	}

	interface Props {
		jobConfig: JobConfig;
		jobSchedule: JobSchedule;
		mode: 'create' | 'edit';
		disabled: boolean;
	}

	let { jobConfig = $bindable(), jobSchedule = $bindable(), mode, disabled } = $props<Props>();

	// Helper functions
	function getInputValue(event: Event): string {
		return (event.target as HTMLInputElement).value;
	}

	function getNumberValue(event: Event): number {
		const value = (event.target as HTMLInputElement).value;
		return value ? parseInt(value) : 0;
	}

	function getFloatValue(event: Event): number {
		const value = (event.target as HTMLInputElement).value;
		return value ? parseFloat(value) : 0;
	}

	function formatDateTime(dateString: string): string {
		if (!dateString) return '';
		try {
			const date = new Date(dateString);
			return date.toISOString().slice(0, 16);
		} catch {
			return '';
		}
	}

	function parseWebUrls(urlString: string): string[] {
		return urlString.split(',').map(url => url.trim()).filter(url => url.length > 0);
	}

	function formatWebUrls(urls: string[]): string {
		return urls.join(', ');
	}
</script>

<div class="space-y-6">
	<!-- Job Identity -->
	<Card class="p-6 bg-slate-900/50 border-slate-800">
		<div class="flex items-center space-x-2 mb-4">
			<Settings class="w-5 h-5 text-blue-400" />
			<h3 class="text-lg font-medium text-white">Job Identity</h3>
		</div>
		<div class="space-y-4">
			<div class="space-y-2">
				<Label for="jobId" class="text-slate-300">Job ID *</Label>
				<Input 
					id="jobId"
					bind:value={jobSchedule.job_id}
					placeholder="Enter unique job identifier"
					class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
					disabled={disabled || mode === 'edit'}
				/>
			</div>
		</div>
	</Card>

	<!-- Job Schedule -->
	<Card class="p-6 bg-slate-900/50 border-slate-800">
		<div class="flex items-center space-x-2 mb-4">
			<Clock class="w-5 h-5 text-green-400" />
			<h3 class="text-lg font-medium text-white">Job Schedule</h3>
		</div>
		<div class="space-y-4">
			<div class="space-y-2">
				<Label for="jobType" class="text-slate-300">Schedule Type</Label>
				<select 
					id="jobType"
					bind:value={jobSchedule.jobType}
					class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
					disabled={disabled || mode === 'edit'}
				>
					<option value="cron">Cron Schedule</option>
					<option value="interval">Interval</option>
					<option value="onetime">One Time</option>
				</select>
			</div>

			<!-- Cron Fields -->
			{#if jobSchedule.jobType === 'cron'}
				<div class="space-y-4 p-4 bg-slate-800/50 rounded-md">
					<h4 class="text-slate-300 font-medium">Cron Schedule Configuration</h4>
					
					<div class="space-y-2">
						<Label for="cronExpression" class="text-slate-300">Cron Expression (optional)</Label>
						<Input 
							id="cronExpression"
							bind:value={jobSchedule.cron_expression}
							placeholder="0 0 * * * (leave empty to use hour/minute/day fields)"
							class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
							disabled={disabled}
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
								bind:value={jobSchedule.hour}
								class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
								disabled={disabled}
							/>
						</div>
						<div class="space-y-2">
							<Label for="minute" class="text-slate-300">Minute (0-59)</Label>
							<Input 
								id="minute"
								type="number"
								min="0"
								max="59"
								bind:value={jobSchedule.minute}
								class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
								disabled={disabled}
							/>
						</div>
						<div class="space-y-2">
							<Label for="dayOfWeek" class="text-slate-300">Day of Week</Label>
							<select 
								id="dayOfWeek"
								bind:value={jobSchedule.day_of_week}
								class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
								disabled={disabled}
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
			{#if jobSchedule.jobType === 'interval'}
				<div class="space-y-4 p-4 bg-slate-800/50 rounded-md">
					<h4 class="text-slate-300 font-medium">Interval Configuration</h4>
					
					<div class="grid grid-cols-3 gap-4">
						<div class="space-y-2">
							<Label for="minutes" class="text-slate-300">Minutes</Label>
							<Input 
								id="minutes"
								type="number"
								min="0"
								bind:value={jobSchedule.minutes}
								class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
								disabled={disabled}
							/>
						</div>
						<div class="space-y-2">
							<Label for="hours" class="text-slate-300">Hours</Label>
							<Input 
								id="hours"
								type="number"
								min="0"
								bind:value={jobSchedule.hours}
								class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
								disabled={disabled}
							/>
						</div>
						<div class="space-y-2">
							<Label for="days" class="text-slate-300">Days</Label>
							<Input 
								id="days"
								type="number"
								min="0"
								bind:value={jobSchedule.days}
								class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
								disabled={disabled}
							/>
						</div>
					</div>
					<p class="text-sm text-slate-400">Specify at least one time unit (minutes, hours, or days)</p>
				</div>
			{/if}

			<!-- One Time Fields -->
			{#if jobSchedule.jobType === 'onetime'}
				<div class="space-y-4 p-4 bg-slate-800/50 rounded-md">
					<h4 class="text-slate-300 font-medium">One-Time Schedule</h4>
					
					<div class="space-y-2">
						<Label for="runDate" class="text-slate-300">Run Date & Time</Label>
						<Input 
							id="runDate"
							type="datetime-local"
							bind:value={jobSchedule.run_date}
							class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
							disabled={disabled}
						/>
					</div>
				</div>
			{/if}
		</div>
	</Card>

	<!-- Data Sources -->
	<Card class="p-6 bg-slate-900/50 border-slate-800">
		<div class="flex items-center space-x-2 mb-4">
			<Database class="w-5 h-5 text-purple-400" />
			<h3 class="text-lg font-medium text-white">Data Sources</h3>
		</div>
		<div class="space-y-4">
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div class="space-y-2">
					<Label for="dataDir" class="text-slate-300">Data Directory</Label>
					<Input 
						id="dataDir"
						bind:value={jobConfig.data_dir}
						placeholder="data/"
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						disabled={disabled}
					/>
				</div>
				<div class="space-y-2">
					<Label for="dataDirPattern" class="text-slate-300">File Pattern</Label>
					<Input 
						id="dataDirPattern"
						bind:value={jobConfig.data_dir_pattern}
						placeholder="*.md"
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						disabled={disabled}
					/>
				</div>
			</div>
			
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div class="space-y-2">
					<Label for="baseUrl" class="text-slate-300">Base URL</Label>
					<Input 
						id="baseUrl"
						bind:value={jobConfig.base_url}
						placeholder="https://example.com"
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						disabled={disabled}
					/>
				</div>
				<div class="space-y-2">
					<Label for="blogBaseUrl" class="text-slate-300">Blog Base URL</Label>
					<Input 
						id="blogBaseUrl"
						bind:value={jobConfig.blog_base_url}
						placeholder="https://blog.example.com"
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						disabled={disabled}
					/>
				</div>
			</div>

			<div class="space-y-2">
				<Label for="webUrls" class="text-slate-300">Web URLs (comma-separated)</Label>
				<Input 
					id="webUrls"
					value={formatWebUrls(jobConfig.web_urls)}
					placeholder="https://example.com/page1, https://example.com/page2"
					class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
					disabled={disabled}
					oninput={(e) => {
						jobConfig.web_urls = parseWebUrls(getInputValue(e));
					}}
				/>
			</div>
		</div>
	</Card>

	<!-- Vector Store Configuration -->
	<Card class="p-6 bg-slate-900/50 border-slate-800">
		<div class="flex items-center space-x-2 mb-4">
			<Activity class="w-5 h-5 text-cyan-400" />
			<h3 class="text-lg font-medium text-white">Vector Store Configuration</h3>
		</div>
		<div class="space-y-4">
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div class="space-y-2">
					<Label for="collectionName" class="text-slate-300">Collection Name *</Label>
					<Input 
						id="collectionName"
						bind:value={jobConfig.collection_name}
						placeholder="lets_talk_documents"
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						disabled={disabled}
					/>
				</div>
				<div class="space-y-2">
					<Label for="embeddingModel" class="text-slate-300">Embedding Model *</Label>
					<Input 
						id="embeddingModel"
						bind:value={jobConfig.embedding_model}
						placeholder="ollama:snowflake-arctic-embed2:latest"
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						disabled={disabled}
					/>
				</div>
			</div>
		</div>
	</Card>

	<!-- Chunking Configuration -->
	<Card class="p-6 bg-slate-900/50 border-slate-800">
		<div class="flex items-center space-x-2 mb-4">
			<FileText class="w-5 h-5 text-orange-400" />
			<h3 class="text-lg font-medium text-white">Chunking Configuration</h3>
		</div>
		<div class="space-y-4">
			<div class="flex items-center space-x-3">
				<Switch 
					id="useChunking"
					checked={jobConfig.use_chunking}
					onCheckedChange={(checked) => jobConfig.use_chunking = checked}
					disabled={disabled}
				/>
				<Label for="useChunking" class="text-slate-300">Enable Chunking</Label>
			</div>
			
			{#if jobConfig.use_chunking}
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div class="space-y-2">
						<Label for="chunkingStrategy" class="text-slate-300">Chunking Strategy</Label>
						<select 
							id="chunkingStrategy"
							bind:value={jobConfig.chunking_strategy}
							class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
							disabled={disabled}
						>
							<option value="semantic">Semantic</option>
							<option value="text_splitter">Text Splitter</option>
						</select>
					</div>
					<div class="space-y-2">
						<Label for="chunkSize" class="text-slate-300">Chunk Size</Label>
						<Input 
							id="chunkSize"
							type="number"
							min="100"
							max="8000"
							bind:value={jobConfig.chunk_size}
							class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
							disabled={disabled}
						/>
					</div>
				</div>
				
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div class="space-y-2">
						<Label for="chunkOverlap" class="text-slate-300">Chunk Overlap</Label>
						<Input 
							id="chunkOverlap"
							type="number"
							min="0"
							max="1000"
							bind:value={jobConfig.chunk_overlap}
							class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
							disabled={disabled}
						/>
					</div>
					<div class="flex items-center space-x-3">
						<Switch 
							id="adaptiveChunking"
							checked={jobConfig.adaptive_chunking}
							onCheckedChange={(checked) => jobConfig.adaptive_chunking = checked}
							disabled={disabled}
						/>
						<Label for="adaptiveChunking" class="text-slate-300">Adaptive Chunking</Label>
					</div>
				</div>

				{#if jobConfig.chunking_strategy === 'semantic'}
					<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
						<div class="space-y-2">
							<Label for="semanticBreakpointType" class="text-slate-300">Breakpoint Type</Label>
							<select 
								id="semanticBreakpointType"
								bind:value={jobConfig.semantic_breakpoint_type}
								class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
								disabled={disabled}
							>
								<option value="percentile">Percentile</option>
								<option value="standard_deviation">Standard Deviation</option>
								<option value="interquartile">Interquartile</option>
								<option value="gradient">Gradient</option>
							</select>
						</div>
						<div class="space-y-2">
							<Label for="semanticThreshold" class="text-slate-300">Threshold Amount</Label>
							<Input 
								id="semanticThreshold"
								type="number"
								min="0"
								max="100"
								step="0.1"
								bind:value={jobConfig.semantic_breakpoint_threshold_amount}
								class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
								disabled={disabled}
							/>
						</div>
						<div class="space-y-2">
							<Label for="semanticMinChunkSize" class="text-slate-300">Min Chunk Size</Label>
							<Input 
								id="semanticMinChunkSize"
								type="number"
								min="10"
								max="1000"
								bind:value={jobConfig.semantic_min_chunk_size}
								class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
								disabled={disabled}
							/>
						</div>
					</div>
				{/if}
			{/if}
		</div>
	</Card>

	<!-- Processing Configuration -->
	<Card class="p-6 bg-slate-900/50 border-slate-800">
		<div class="flex items-center space-x-2 mb-4">
			<Zap class="w-5 h-5 text-yellow-400" />
			<h3 class="text-lg font-medium text-white">Processing Configuration</h3>
		</div>
		<div class="space-y-4">
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div class="flex items-center space-x-3">
					<Switch 
						id="indexOnlyPublished"
						checked={jobConfig.index_only_published_posts}
						onCheckedChange={(checked) => jobConfig.index_only_published_posts = checked}
						disabled={disabled}
					/>
					<Label for="indexOnlyPublished" class="text-slate-300">Index Only Published Posts</Label>
				</div>
				<div class="flex items-center space-x-3">
					<Switch 
						id="forceRecreate"
						checked={jobConfig.force_recreate}
						onCheckedChange={(checked) => jobConfig.force_recreate = checked}
						disabled={disabled}
					/>
					<Label for="forceRecreate" class="text-slate-300">Force Recreate Vector Store</Label>
				</div>
			</div>
			
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div class="space-y-2">
					<Label for="incrementalMode" class="text-slate-300">Incremental Mode</Label>
					<select 
						id="incrementalMode"
						bind:value={jobConfig.incremental_mode}
						class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
						disabled={disabled}
					>
						<option value="auto">Auto</option>
						<option value="incremental">Incremental</option>
						<option value="full">Full</option>
					</select>
				</div>
				<div class="space-y-2">
					<Label for="checksumAlgorithm" class="text-slate-300">Checksum Algorithm</Label>
					<select 
						id="checksumAlgorithm"
						bind:value={jobConfig.checksum_algorithm}
						class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
						disabled={disabled}
					>
						<option value="sha256">SHA256</option>
						<option value="md5">MD5</option>
					</select>
				</div>
			</div>
			
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div class="flex items-center space-x-3">
					<Switch 
						id="autoDetectChanges"
						checked={jobConfig.auto_detect_changes}
						onCheckedChange={(checked) => jobConfig.auto_detect_changes = checked}
						disabled={disabled}
					/>
					<Label for="autoDetectChanges" class="text-slate-300">Auto Detect Changes</Label>
				</div>
				<div class="space-y-2">
					<Label for="incrementalFallbackThreshold" class="text-slate-300">Incremental Fallback Threshold</Label>
					<Input 
						id="incrementalFallbackThreshold"
						type="number"
						min="0"
						max="1"
						step="0.1"
						bind:value={jobConfig.incremental_fallback_threshold}
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						disabled={disabled}
					/>
				</div>
			</div>
		</div>
	</Card>

	<!-- Performance Configuration -->
	<Card class="p-6 bg-slate-900/50 border-slate-800">
		<div class="flex items-center space-x-2 mb-4">
			<Activity class="w-5 h-5 text-green-400" />
			<h3 class="text-lg font-medium text-white">Performance Configuration</h3>
		</div>
		<div class="space-y-4">
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div class="flex items-center space-x-3">
					<Switch 
						id="enableBatchProcessing"
						checked={jobConfig.enable_batch_processing}
						onCheckedChange={(checked) => jobConfig.enable_batch_processing = checked}
						disabled={disabled}
					/>
					<Label for="enableBatchProcessing" class="text-slate-300">Enable Batch Processing</Label>
				</div>
				<div class="flex items-center space-x-3">
					<Switch 
						id="enablePerformanceMonitoring"
						checked={jobConfig.enbable_performance_monitoring}
						onCheckedChange={(checked) => jobConfig.enbable_performance_monitoring = checked}
						disabled={disabled}
					/>
					<Label for="enablePerformanceMonitoring" class="text-slate-300">Enable Performance Monitoring</Label>
				</div>
			</div>
			
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				<div class="space-y-2">
					<Label for="batchSize" class="text-slate-300">Batch Size</Label>
					<Input 
						id="batchSize"
						type="number"
						min="1"
						max="1000"
						bind:value={jobConfig.batch_size}
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						disabled={disabled}
					/>
				</div>
				<div class="space-y-2">
					<Label for="batchPauseSeconds" class="text-slate-300">Batch Pause (seconds)</Label>
					<Input 
						id="batchPauseSeconds"
						type="number"
						min="0"
						max="10"
						step="0.1"
						bind:value={jobConfig.batch_pause_seconds}
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						disabled={disabled}
					/>
				</div>
				<div class="space-y-2">
					<Label for="maxConcurrentOps" class="text-slate-300">Max Concurrent Operations</Label>
					<Input 
						id="maxConcurrentOps"
						type="number"
						min="1"
						max="20"
						bind:value={jobConfig.max_concurrent_operations}
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						disabled={disabled}
					/>
				</div>
			</div>
		</div>
	</Card>

	<!-- Output Configuration -->
	<Card class="p-6 bg-slate-900/50 border-slate-800">
		<div class="flex items-center space-x-2 mb-4">
			<FileText class="w-5 h-5 text-indigo-400" />
			<h3 class="text-lg font-medium text-white">Output Configuration</h3>
		</div>
		<div class="space-y-4">
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div class="space-y-2">
					<Label for="metadataCsv" class="text-slate-300">Metadata CSV</Label>
					<Input 
						id="metadataCsv"
						bind:value={jobConfig.metadata_csv}
						placeholder="blog_metadata.csv"
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						disabled={disabled}
					/>
				</div>
				<div class="space-y-2">
					<Label for="blogStatsFilename" class="text-slate-300">Blog Stats Filename</Label>
					<Input 
						id="blogStatsFilename"
						bind:value={jobConfig.blog_stats_filename}
						placeholder="blog_stats_latest.json"
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						disabled={disabled}
					/>
				</div>
			</div>
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div class="space-y-2">
					<Label for="blogDocsFilename" class="text-slate-300">Blog Docs Filename</Label>
					<Input 
						id="blogDocsFilename"
						bind:value={jobConfig.blog_docs_filename}
						placeholder="blog_docs.csv"
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						disabled={disabled}
					/>
				</div>
				<div class="space-y-2">
					<Label for="healthReportFilename" class="text-slate-300">Health Report Filename</Label>
					<Input 
						id="healthReportFilename"
						bind:value={jobConfig.health_report_filename}
						placeholder="health_report.json"
						class="bg-slate-800 border-slate-700 text-white placeholder-slate-400"
						disabled={disabled}
					/>
				</div>
			</div>
		</div>
	</Card>
</div>