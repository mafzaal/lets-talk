<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		id?: string;
		type?: string;
		value?: string;
		placeholder?: string;
		disabled?: boolean;
		class?: string;
		oninput?: (e: Event) => void;
		min?: string;
		max?: string;
		step?: string;
	}

	let { id, type = 'text', value = $bindable(''), placeholder, disabled = false, class: className = '', oninput, min, max, step, ...restProps }: Props = $props();
</script>

<input
	{id}
	{type}
	bind:value
	{placeholder}
	{disabled}
	{oninput}
	{min}
	{max}
	{step}
	{...restProps}
	class={cn(
		'flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:ring-offset-slate-950 dark:placeholder:text-slate-400 dark:focus-visible:ring-slate-300',
		className
	)}
/>