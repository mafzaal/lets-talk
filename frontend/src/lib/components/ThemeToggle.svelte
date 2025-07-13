<script lang="ts">
	import { themeStore } from '$lib/stores/theme';
	import Button from '$lib/components/ui/button.svelte';
	import { Sun, Moon } from 'lucide-svelte';

	let currentTheme = $state('dark');

	// Subscribe to theme changes
	themeStore.subscribe((theme) => {
		currentTheme = theme;
	});

	function toggleTheme() {
		themeStore.toggle();
	}
</script>

<Button
	variant="ghost"
	size="icon"
	onclick={toggleTheme}
	class="h-8 w-8 hover:bg-accent hover:text-accent-foreground"
	aria-label="Toggle theme"
>
	{#if currentTheme === 'dark'}
		<Sun class="h-4 w-4" />
	{:else}
		<Moon class="h-4 w-4" />
	{/if}
</Button>