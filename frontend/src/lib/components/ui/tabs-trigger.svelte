<script lang="ts">
	import { getContext } from 'svelte';
	import { cn } from '$lib/utils';

	interface Props {
		value: string;
		class?: string;
		children?: any;
	}

	let { value, class: className = '', children, ...restProps }: Props = $props();

	const tabs = getContext('tabs') as {
		activeTab: () => string;
		setActiveTab: (tab: string) => void;
	};

	function handleClick() {
		tabs.setActiveTab(value);
	}

	let isActive = $derived(tabs.activeTab() === value);
</script>

<button
	type="button"
	onclick={handleClick}
	{...restProps}
	class={cn(
		'inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 dark:ring-offset-slate-950 dark:focus-visible:ring-slate-300',
		isActive
			? 'bg-white text-slate-950 shadow-sm dark:bg-slate-950 dark:text-slate-50'
			: 'hover:bg-slate-200 dark:hover:bg-slate-700',
		className
	)}
>
	{@render children()}
</button>