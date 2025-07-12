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
	class={cn('flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2', className)}
>
	{@render children()}
</div>