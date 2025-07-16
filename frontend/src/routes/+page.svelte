<script lang="ts">
	import { MessageCircle, Calendar, Settings, ArrowRight, ChartColumn } from 'lucide-svelte';
</script>

<div class="min-h-screen">
	<div class="container mx-auto px-4 py-16">
		<!-- Header -->
		<div class="text-center mb-12">
			<div class="flex justify-center mb-6">
				<div class="w-16 h-16 bg-blue-600 rounded-xl flex items-center justify-center">
					<MessageCircle class="w-8 h-8 text-white" />
				</div>
			</div>
			<h1 class="text-4xl font-bold mb-4">Welcome to Let's Talk</h1>
			<p class="text-xl text-slate-400 max-w-2xl mx-auto">
				AI-powered chat system with comprehensive pipeline management and analytics
			</p>
		</div>

		<!-- Quick Actions -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
			<a
				href="/dashboard"
				class="p-6 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition-colors group"
			>
				<div class="flex items-center justify-between mb-4">
					<ChartColumn class="w-8 h-8 text-blue-400" />
					<ArrowRight class="w-4 h-4 text-slate-400 group-hover:text-white transition-colors" />
				</div>
				<h3 class="text-lg font-medium text-white mb-2">Dashboard</h3>
				<p class="text-sm text-slate-400">View system status and analytics</p>
			</a>

			<a
				href="/jobs"
				class="p-6 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition-colors group"
			>
				<div class="flex items-center justify-between mb-4">
					<Settings class="w-8 h-8 text-green-400" />
					<ArrowRight class="w-4 h-4 text-slate-400 group-hover:text-white transition-colors" />
				</div>
				<h3 class="text-lg font-medium text-white mb-2">Jobs</h3>
				<p class="text-sm text-slate-400">Manage pipeline jobs and schedules</p>
			</a>

			<a
				href="/analytics"
				class="p-6 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition-colors group"
			>
				<div class="flex items-center justify-between mb-4">
					<ChartColumn class="w-8 h-8 text-purple-400" />
					<ArrowRight class="w-4 h-4 text-slate-400 group-hover:text-white transition-colors" />
				</div>
				<h3 class="text-lg font-medium text-white mb-2">Analytics</h3>
				<p class="text-sm text-slate-400">Performance insights and trends</p>
			</a>

			<a
				href="/activity"
				class="p-6 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition-colors group"
			>
				<div class="flex items-center justify-between mb-4">
					<Calendar class="w-8 h-8 text-orange-400" />
					<ArrowRight class="w-4 h-4 text-slate-400 group-hover:text-white transition-colors" />
				</div>
				<h3 class="text-lg font-medium text-white mb-2">Activity</h3>
				<p class="text-sm text-slate-400">Real-time system activity feed</p>
			</a>
		</div>
	</div>
</div>
