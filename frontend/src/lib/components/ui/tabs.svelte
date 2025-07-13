<script lang="ts">
	import { setContext } from 'svelte';
	import { cn } from '$lib/utils';

	interface Props {
		defaultValue?: string;
		value?: string;
		class?: string;
		children?: any;
	}

	let { defaultValue, value = defaultValue || '', class: className = '', children, ...restProps }: Props = $props();

	let activeTab = $state(value);

	setContext('tabs', {
		activeTab: () => activeTab,
		setActiveTab: (tab: string) => {
			activeTab = tab;
		}
	});

	$effect(() => {
		if (value !== activeTab) {
			activeTab = value;
		}
	});
</script>

<div
	{...restProps}
	class={cn('w-full', className)}
>
	{@render children()}
</div>