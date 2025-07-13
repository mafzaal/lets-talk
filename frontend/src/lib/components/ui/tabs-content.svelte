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

	let isActive = $derived(tabs.activeTab() === value);
</script>

{#if isActive}
	<div
		{...restProps}
		class={cn(
			'mt-2 ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 dark:ring-offset-slate-950 dark:focus-visible:ring-slate-300',
			className
		)}
	>
		{@render children()}
	</div>
{/if}