<script lang="ts">
	import { cn } from '$lib/utils';
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
		class?: string;
		variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'ghost' | 'link';
		size?: 'default' | 'sm' | 'lg' | 'icon';
		[key: string]: any;
	}

	let { 
		children, 
		class: className, 
		variant = 'default', 
		size = 'default',
		...props 
	}: Props = $props();

	const variants = {
		default: 'bg-slate-900 text-slate-50 hover:bg-slate-900/90',
		secondary: 'bg-slate-100 text-slate-900 hover:bg-slate-100/80',
		destructive: 'bg-red-500 text-slate-50 hover:bg-red-500/90',
		outline: 'border border-slate-200 bg-background hover:bg-slate-100 hover:text-slate-900',
		ghost: 'hover:bg-slate-100 hover:text-slate-900',
		link: 'text-slate-900 underline-offset-4 hover:underline',
	};

	const sizes = {
		default: 'h-10 px-4 py-2',
		sm: 'h-9 rounded-md px-3',
		lg: 'h-11 rounded-md px-8',
		icon: 'h-10 w-10',
	};
</script>

<button
	class={cn(
		'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
		variants[variant],
		sizes[size],
		className
	)}
	{...props}
>
	{@render children()}
</button>