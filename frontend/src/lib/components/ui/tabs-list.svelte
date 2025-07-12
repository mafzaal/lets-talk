<script lang="ts">
	import { getContext } from 'svelte';
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		children?: any;
	}

	let { class: className = '', children, ...restProps }: Props = $props();

	const tabs = getContext('tabs') as {
		activeTab: () => string;
		setActiveTab: (tab: string) => void;
	};
</script>

<div
	{...restProps}
	class={cn(
		'inline-flex h-10 items-center justify-center rounded-md bg-slate-100 p-1 text-slate-500 dark:bg-slate-800 dark:text-slate-400',
		className
	)}
>
	{@render children()}
</div>