<script lang="ts">
	import { page } from '$app/state';
	import { cn } from '$lib/utils';
	import SystemStatus from '$lib/components/SystemStatus.svelte';
	import {
		Home,
		Settings,
		Activity,
		Calendar,
		MessageCircle,
		Users,
		Play,
		Pause,
		Plus,
		ChartColumn
	} from 'lucide-svelte';
	import Button from '$lib/components/ui/button.svelte';
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();

	const navigation = [
		{ name: 'Dashboard', href: '/dashboard', icon: Home },
		{ name: 'Jobs', href: '/jobs', icon: Settings },
		{ name: 'Analytics', href: '/analytics', icon: ChartColumn },
		{ name: 'Activity', href: '/activity', icon: Activity },
		{ name: 'Chat', href: '/', icon: MessageCircle }
	];

	function isCurrentPage(href: string) {
		return page.url.pathname === href;
	}
</script>

<div class="flex h-screen bg-slate-950">
	<!-- Sidebar -->
	<div class="flex flex-col w-64 bg-slate-900 border-r border-slate-800">
		<!-- Logo -->
		<div class="flex items-center h-16 px-6 border-b border-slate-800">
			<div class="flex items-center space-x-2">
				<div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
					<MessageCircle class="w-5 h-5 text-white" />
				</div>
				<span class="text-xl font-bold text-white">Let's Talk</span>
			</div>
		</div>

		<!-- Navigation -->
		<nav class="flex-1 px-4 py-6 space-y-2">
			{#each navigation as item}
				{@const Icon = item.icon}
				<a
					href={item.href}
					class={cn(
						'flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
						isCurrentPage(item.href)
							? 'bg-slate-800 text-white'
							: 'text-slate-400 hover:text-white hover:bg-slate-800'
					)}
				>
					<Icon class="w-5 h-5" />
					<span>{item.name}</span>
				</a>
			{/each}
		</nav>

		<!-- Bottom actions -->
		<div class="p-4 border-t border-slate-800">
			<Button variant="outline" class="w-full text-slate-400 border-slate-700 hover:bg-slate-800">
				<Plus class="w-4 h-4 mr-2" />
				New Job
			</Button>
		</div>
	</div>

	<!-- Main content -->
	<div class="flex-1 flex flex-col overflow-hidden">
		<!-- Header -->
		<header
			class="flex items-center justify-between h-16 px-6 border-b border-slate-800 bg-slate-900"
		>
			<div class="flex items-center space-x-4">
				<h1 class="text-xl font-semibold text-white">
					{#if page.url.pathname === '/dashboard'}
						Dashboard
					{:else if page.url.pathname === '/jobs'}
						Jobs
					{:else if page.url.pathname === '/analytics'}
						Analytics
					{:else if page.url.pathname === '/activity'}
						Activity
					{:else}
						Chat
					{/if}
				</h1>
			</div>
			<div class="flex items-center space-x-4">
				<SystemStatus />
			</div>
		</header>

		<!-- Main content area -->
		<main class="flex-1 overflow-auto p-6 bg-slate-950">
			{@render children()}
		</main>
	</div>
</div>
