<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		children?: any;
	}

	let { class: className = '', children, ...restProps }: Props = $props();
</script>

<p
	{...restProps}
	class={cn('text-sm text-slate-500 dark:text-slate-400', className)}
>
	{@render children()}
</p>