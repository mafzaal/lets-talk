<script lang="ts">
	import { page } from '$app/state';
	import SystemStatus from '$lib/components/SystemStatus.svelte';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import { Home, Settings, Activity, Calendar, MessageCircle, ChartColumn } from 'lucide-svelte';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';

	const navigation = [
		{ name: 'Dashboard', href: '/dashboard', icon: Home },
		{ name: 'Jobs', href: '/jobs', icon: Calendar },
		{ name: 'Analytics', href: '/analytics', icon: ChartColumn },
		{ name: 'Activity', href: '/activity', icon: Activity }
	];

	function isCurrentPage(href: string) {
		return page.url.pathname === href;
	}
</script>

<Sidebar.Root>
	<Sidebar.Header>
		<div class="flex items-center space-x-2 py-5">
			<div class="w-8 h-8 rounded-lg flex items-center justify-center">
				<MessageCircle class="w-5 h-5" />
			</div>
			<span class="text-xl font-bold">Let's Talk</span>
		</div>
	</Sidebar.Header>
	<Sidebar.Content>
		<Sidebar.Group>
			<Sidebar.GroupLabel>Menu</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each navigation as item (item.name)}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton isActive={isCurrentPage(item.href)}>
								{#snippet child({ props })}
									<a href={item.href} {...props}>
										<item.icon />
										<span>{item.name}</span>
									</a>
								{/snippet}
							</Sidebar.MenuButton>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>
	</Sidebar.Content>
	<Sidebar.Footer>
		<div class="flex items-left gap-2 justify-between flex-col pt-4 pl-4 border-t">
			<div class="flex items-center justify-between">
				<a href="/settings" class="flex items-center text-sm">
					<Settings class="w-4 h-4 mr-2" />
					<span>Settings</span>
				</a>
				<ThemeToggle />
			</div>
			<div class="flex items-center space-x-4">
				<SystemStatus />
			</div>
		</div>
	</Sidebar.Footer>
</Sidebar.Root>
