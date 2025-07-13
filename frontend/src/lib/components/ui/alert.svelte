<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		variant?: 'default' | 'destructive';
		class?: string;
		children?: any;
	}

	let { variant = 'default', class: className = '', children, ...restProps }: Props = $props();

	const variants = {
		default: 'border-slate-200 text-slate-950 dark:border-slate-800 dark:text-slate-50',
		destructive: 'border-red-200 text-red-900 dark:border-red-800 dark:text-red-50'
	};
</script>

<div
	{...restProps}
	class={cn(
		'relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-slate-950 dark:[&>svg]:text-slate-50',
		variants[variant],
		className
	)}
>
	{@render children()}
</div>