<script lang="ts">
	import { cn } from '$lib/utils';
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
		class?: string;
		[key: string]: any;
	}

	let { children, class: className, ...props }: Props = $props();
</script>

<div
	class={cn('flex h-5 items-center space-x-4 text-sm', className)}
	{...props}
>
	{@render children()}
</div>