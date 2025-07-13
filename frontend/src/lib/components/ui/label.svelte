<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		for?: string;
		class?: string;
		children?: any;
	}

	let { for: htmlFor, class: className = '', children, ...restProps }: Props = $props();
</script>

<label
	for={htmlFor}
	{...restProps}
	class={cn(
		'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
		className
	)}
>
	{@render children()}
</label>