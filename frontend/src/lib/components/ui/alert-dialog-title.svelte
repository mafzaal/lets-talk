<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		children?: any;
	}

	let { class: className = '', children, ...restProps }: Props = $props();
</script>

<h2
	{...restProps}
	class={cn('text-lg font-semibold', className)}
>
	{@render children()}
</h2>