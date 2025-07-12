<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		children?: any;
	}

	let { class: className = '', children, ...restProps }: Props = $props();
</script>

<div
	{...restProps}
	class={cn('', className)}
>
	{@render children()}
</div>