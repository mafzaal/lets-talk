<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		checked?: boolean;
		disabled?: boolean;
		class?: string;
		onCheckedChange?: (checked: boolean) => void;
		id?: string;
	}

	let { checked = false, disabled = false, class: className = '', onCheckedChange, id, ...restProps }: Props = $props();

	function handleChange(e: Event) {
		const target = e.target as HTMLInputElement;
		onCheckedChange?.(target.checked);
	}
</script>

<label class={cn('relative inline-flex items-center cursor-pointer', className)}>
	<input
		type="checkbox"
		{id}
		{checked}
		{disabled}
		onchange={handleChange}
		{...restProps}
		class="sr-only peer"
	/>
	<div
		class="relative w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-slate-600 peer-checked:bg-blue-600"
	></div>
</label>