const API_BASE_URL = 'http://localhost:8000';

export interface JobConfig {
	data_dir: string;
	data_dir_pattern: string;
	web_urls: string[];
	base_url: string;
	blog_base_url: string;
	index_only_published_posts: boolean;
	use_chunking: boolean;
	chunking_strategy: 'semantic' | 'text_splitter';
	adaptive_chunking: boolean;
	chunk_size: number;
	chunk_overlap: number;
	semantic_breakpoint_type: 'percentile' | 'standard_deviation' | 'interquartile' | 'gradient';
	semantic_breakpoint_threshold_amount: number;
	semantic_min_chunk_size: number;
	collection_name: string;
	embedding_model: string;
	force_recreate: boolean;
	incremental_mode: string;
	checksum_algorithm: string;
	auto_detect_changes: boolean;
	incremental_fallback_threshold: number;
	enable_batch_processing: boolean;
	batch_size: number;
	enbable_performance_monitoring: boolean;
	batch_pause_seconds: number;
	max_concurrent_operations: number;
	max_backup_files: number;
	metadata_csv: string;
	blog_stats_filename: string;
	blog_docs_filename: string;
	health_report_filename: string;
	ci_summary_filename: string;
	build_info_filename: string;
	job_id?: string;
}

export interface JobResponse {
	id: string;
	name: string;
	next_run_time?: string;
	trigger: string;
	config: Record<string, any>;
}

export interface SchedulerStats {
	jobs_executed: number;
	jobs_failed: number;
	jobs_missed: number;
	last_execution?: string;
	last_error?: Record<string, any>;
	active_jobs: number;
	scheduler_running: boolean;
}

export interface HealthStatus {
	status: string;
	timestamp: string;
	scheduler_status: string;
	version: string;
}

export interface PipelineReport {
	job_id: string;
	execution_time: string;
	status: string;
	duration: number;
	total_documents: number;
	errors: string[];
	warnings: string[];
}

class ApiClient {
	private baseUrl: string;

	constructor(baseUrl: string = API_BASE_URL) {
		this.baseUrl = baseUrl;
	}

	private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
		const url = `${this.baseUrl}${endpoint}`;
		const response = await fetch(url, {
			headers: {
				'Content-Type': 'application/json',
				...options.headers,
			},
			...options,
		});

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		return await response.json();
	}

	// Health endpoints
	async getHealth(): Promise<HealthStatus> {
		return this.request<HealthStatus>('/health');
	}

	// Scheduler endpoints
	async getSchedulerStats(): Promise<SchedulerStats> {
		return this.request<SchedulerStats>('/scheduler/status');
	}

	async getJobs(): Promise<JobResponse[]> {
		return this.request<JobResponse[]>('/scheduler/jobs');
	}

	async createCronJob(data: {
		job_id: string;
		hour?: number;
		minute?: number;
		day_of_week?: string;
		cron_expression?: string;
		config?: JobConfig;
	}): Promise<JobResponse> {
		return this.request<JobResponse>('/scheduler/jobs/cron', {
			method: 'POST',
			body: JSON.stringify(data),
		});
	}

	async createIntervalJob(data: {
		job_id: string;
		minutes?: number;
		hours?: number;
		days?: number;
		config?: JobConfig;
	}): Promise<JobResponse> {
		return this.request<JobResponse>('/scheduler/jobs/interval', {
			method: 'POST',
			body: JSON.stringify(data),
		});
	}

	async deleteJob(jobId: string): Promise<void> {
		await this.request(`/scheduler/jobs/${jobId}`, {
			method: 'DELETE',
		});
	}

	// Pipeline endpoints
	async runPipeline(config?: JobConfig): Promise<{ message: string; job_id: string }> {
		return this.request<{ message: string; job_id: string }>('/pipeline/run', {
			method: 'POST',
			body: JSON.stringify({ config }),
		});
	}

	async getPipelineReports(): Promise<{ reports: PipelineReport[] }> {
		return this.request<{ reports: PipelineReport[] }>('/pipeline/reports');
	}
}

export const apiClient = new ApiClient();