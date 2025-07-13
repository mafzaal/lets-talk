<script lang="ts">
	import { onMount } from 'svelte';
	import { apiClient } from '$lib/api';
	import type { SettingDisplay, SettingsResponse, SettingUpdate } from '$lib/api';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Label from '$lib/components/ui/label.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import Switch from '$lib/components/ui/switch.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import AlertDescription from '$lib/components/ui/alert-description.svelte';
	import AlertDialog from '$lib/components/ui/alert-dialog.svelte';
	import AlertDialogContent from '$lib/components/ui/alert-dialog-content.svelte';
	import AlertDialogHeader from '$lib/components/ui/alert-dialog-header.svelte';
	import AlertDialogTitle from '$lib/components/ui/alert-dialog-title.svelte';
	import AlertDialogDescription from '$lib/components/ui/alert-dialog-description.svelte';
	import AlertDialogFooter from '$lib/components/ui/alert-dialog-footer.svelte';
	import { Separator } from '$lib/components/ui/separator';
	import { toast } from 'svelte-sonner';
	import { Eye, EyeOff, Save, RotateCcw, Settings, Lock, Unlock, AlertCircle, Info } from 'lucide-svelte';

	let settings = $state<SettingDisplay[]>([]);
	let sections = $state<string[]>([]);
	let loading = $state(true);
	let saving = $state(false);
	let restoring = $state(false);
	let pendingChanges = $state(new Map<string, string>());
	let secretVisibility = $state(new Map<string, boolean>());
	let error = $state('');
	let showRestoreDialog = $state(false);

	// Group settings by section
	let settingsBySection = $derived(() => {
		const grouped = new Map<string, SettingDisplay[]>();
		settings.forEach((setting) => {
			const sectionSettings = grouped.get(setting.section) || [];
			sectionSettings.push(setting);
			grouped.set(setting.section, sectionSettings);
		});
		return grouped;
	});

	// Check if there are any pending changes
	let hasChanges = $derived(pendingChanges.size > 0);

	onMount(async () => {
		await loadSettings();
	});

	async function loadSettings() {
		try {
			loading = true;
			error = '';
			console.log('Starting to load settings...');
			const response = await apiClient.getSettings();
			console.log('Settings response:', response);
			settings = response.settings;
			sections = response.sections;
			console.log('Settings loaded:', settings.length, 'sections:', sections.length);
		} catch (err) {
			console.error('Error loading settings:', err);
			error = err instanceof Error ? err.message : 'Failed to load settings';
			toast.error('Failed to load settings');
		} finally {
			loading = false;
			console.log(
				'Loading complete. loading:',
				loading,
				'settings:',
				settings.length,
				'sections:',
				sections.length
			);
			// Force a re-render by updating the DOM
			requestAnimationFrame(() => {
				console.log('Animation frame - loading:', loading, 'settings:', settings.length);
			});
		}
	}

	function handleInputChange(key: string, value: string) {
		const originalSetting = settings.find((s) => s.key === key);
		if (originalSetting && originalSetting.value !== value) {
			pendingChanges.set(key, value);
		} else {
			pendingChanges.delete(key);
		}
		// Trigger reactivity
		pendingChanges = new Map(pendingChanges);
	}

	function toggleSecretVisibility(key: string) {
		secretVisibility.set(key, !secretVisibility.get(key));
		// Trigger reactivity
		secretVisibility = new Map(secretVisibility);
	}

	function getDisplayValue(setting: SettingDisplay): string {
		if (pendingChanges.has(setting.key)) {
			return pendingChanges.get(setting.key)!;
		}
		return setting.value;
	}

	function getActualValue(setting: SettingDisplay): string {
		if (setting.is_secret && !secretVisibility.get(setting.key)) {
			return '***HIDDEN***';
		}
		return getDisplayValue(setting);
	}

	async function saveSettings() {
		if (pendingChanges.size === 0) return;

		try {
			saving = true;
			const updates: SettingUpdate[] = Array.from(pendingChanges.entries()).map(([key, value]) => ({
				key,
				value
			}));

			const response = await apiClient.updateSettings({ settings: updates });

			if (response.success) {
				toast.success(`Updated ${response.updated_settings.length} settings`);
				pendingChanges.clear();
				pendingChanges = new Map();
				await loadSettings(); // Reload to get updated values
			} else {
				toast.error(response.message);
				if (response.failed_settings.length > 0) {
					const failedMessages = response.failed_settings.map((f) => `${f.key}: ${f.error}`);
					toast.error(`Failed: ${failedMessages.join(', ')}`);
				}
			}
		} catch (err) {
			toast.error('Failed to save settings');
		} finally {
			saving = false;
		}
	}

	async function restoreDefaults() {
		showRestoreDialog = true;
	}

	async function confirmRestoreDefaults() {
		showRestoreDialog = false;

		try {
			restoring = true;
			const response = await apiClient.restoreDefaultSettings();

			if (response.success) {
				toast.success(`Restored ${response.restored_count} settings to defaults`);
				pendingChanges.clear();
				pendingChanges = new Map();
				await loadSettings();
			} else {
				toast.error(response.message);
			}
		} catch (err) {
			toast.error('Failed to restore defaults');
		} finally {
			restoring = false;
		}
	}

	function cancelRestoreDefaults() {
		showRestoreDialog = false;
	}

	function discardChanges() {
		pendingChanges.clear();
		pendingChanges = new Map();
		toast.info('Changes discarded');
	}
</script>

<svelte:head>
	<title>System Settings - Let's Talk</title>
</svelte:head>

<div class="container mx-auto max-w-6xl space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div class="space-y-1">
			<h1 class="text-3xl font-bold flex items-center gap-2">
				<Settings class="w-8 h-8" />
				System Settings
			</h1>
			<p class="text-muted-foreground">Configure system behavior and application settings</p>
		</div>
		<div class="flex items-center gap-2">
			{#if hasChanges}
				<Button variant="outline" onclick={discardChanges}>
					Discard Changes
				</Button>
			{/if}
			<Button variant="outline" onclick={restoreDefaults} disabled={restoring}>
				{#if restoring}
					<RotateCcw class="w-4 h-4 mr-2 animate-spin" />
				{:else}
					<RotateCcw class="w-4 h-4 mr-2" />
				{/if}
				Restore Defaults
			</Button>
			<Button onclick={saveSettings} disabled={!hasChanges || saving}>
				{#if saving}
					<Save class="w-4 h-4 mr-2 animate-spin" />
				{:else}
					<Save class="w-4 h-4 mr-2" />
				{/if}
				Save Changes
			</Button>
		</div>
	</div>

	{#if error}
		<Alert variant="destructive">
			<AlertCircle class="h-4 w-4" />
			<AlertDescription>{error}</AlertDescription>
		</Alert>
	{/if}

	<!-- Change notification -->
	{#if hasChanges}
		<Alert>
			<Info class="h-4 w-4" />
			<AlertDescription>
				You have {pendingChanges.size} unsaved changes. Don't forget to save them.
			</AlertDescription>
		</Alert>
	{/if}

	{#if loading}
		<div class="flex flex-col items-center justify-center py-12 space-y-4">
			<div class="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full"></div>
			<p class="text-muted-foreground">Loading settings...</p>
		</div>
	{:else if settings.length > 0}
		<div class="space-y-6">
			{#each sections as section}
				<Card class="border-border bg-card">
					<div class="p-6">
						<h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
							{section}
							<Badge variant="secondary" class="text-xs">
								{settingsBySection().get(section)?.length || 0} settings
							</Badge>
						</h2>
						
						<Separator class="mb-6" />
						
						<div class="space-y-6">
							{#each settingsBySection().get(section) || [] as setting}
								<div class="space-y-3">
									<div class="flex items-center justify-between">
										<Label for={setting.key} class="text-sm font-medium flex items-center gap-2">
											{setting.key}
											{#if setting.is_secret}
												<Badge variant="destructive" class="text-xs">
													<Lock class="w-3 h-3 mr-1" />
													Secret
												</Badge>
											{/if}
											{#if setting.is_read_only}
												<Badge variant="outline" class="text-xs">
													<Lock class="w-3 h-3 mr-1" />
													Read-only
												</Badge>
											{:else}
												<Badge variant="secondary" class="text-xs">
													<Unlock class="w-3 h-3 mr-1" />
													Editable
												</Badge>
											{/if}
										</Label>
									</div>

									{#if setting.description}
										<p class="text-sm text-muted-foreground">{setting.description}</p>
									{/if}

									<div class="flex items-center gap-2">
										{#if setting.data_type === 'boolean'}
											<Switch
												id={setting.key}
												checked={getDisplayValue(setting) === 'true'}
												onCheckedChange={(checked) =>
													handleInputChange(setting.key, checked.toString())}
												disabled={setting.is_read_only}
											/>
										{:else}
											<div class="flex-1 relative">
												<Input
													id={setting.key}
													type={setting.is_secret && !secretVisibility.get(setting.key)
														? 'password'
														: 'text'}
													value={getActualValue(setting)}
													oninput={(e) => handleInputChange(setting.key, (e.target as HTMLInputElement)?.value || '')}
													disabled={setting.is_read_only}
													placeholder={setting.default_value}
													class={`${pendingChanges.has(setting.key) ? 'border-yellow-500 ring-yellow-500' : ''}`}
												/>
												{#if setting.is_secret}
													<button
														type="button"
														class="absolute inset-y-0 right-0 pr-3 flex items-center hover:text-foreground transition-colors"
														onclick={() => toggleSecretVisibility(setting.key)}
													>
														{#if secretVisibility.get(setting.key)}
															<EyeOff class="w-4 h-4 text-muted-foreground" />
														{:else}
															<Eye class="w-4 h-4 text-muted-foreground" />
														{/if}
													</button>
												{/if}
											</div>
										{/if}
									</div>

									{#if setting.default_value !== getDisplayValue(setting)}
										<p class="text-xs text-muted-foreground">
											Default: {setting.default_value}
										</p>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				</Card>
			{/each}
		</div>
	{:else}
		<div class="flex flex-col items-center justify-center py-12 space-y-4">
			<Settings class="w-16 h-16 text-muted-foreground" />
			<p class="text-muted-foreground">No settings found.</p>
		</div>
	{/if}
</div>

<!-- Restore Defaults Confirmation Dialog -->
<AlertDialog open={showRestoreDialog} onOpenChange={(open) => (showRestoreDialog = open)}>
	<AlertDialogContent>
		{#snippet children()}
			<AlertDialogHeader>
				{#snippet children()}
					<AlertDialogTitle>
						{#snippet children()}
							Restore Default Settings
						{/snippet}
					</AlertDialogTitle>
					<AlertDialogDescription>
						{#snippet children()}
							Are you sure you want to restore all settings to their default values? This action
							cannot be undone and will override any customizations you've made.
						{/snippet}
					</AlertDialogDescription>
				{/snippet}
			</AlertDialogHeader>
			<AlertDialogFooter>
				{#snippet children()}
					<Button variant="outline" onclick={cancelRestoreDefaults}>Cancel</Button>
					<Button variant="destructive" onclick={confirmRestoreDefaults} disabled={restoring}>
						{#if restoring}
							<RotateCcw class="w-4 h-4 mr-2 animate-spin" />
						{:else}
							<RotateCcw class="w-4 h-4 mr-2" />
						{/if}
						Restore Defaults
					</Button>
				{/snippet}
			</AlertDialogFooter>
		{/snippet}
	</AlertDialogContent>
</AlertDialog>
