import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type Theme = 'light' | 'dark';

// Initialize theme from localStorage or default to dark
function createThemeStore() {
	const defaultTheme: Theme = 'dark';
	const initialTheme = browser 
		? (localStorage.getItem('theme') as Theme) || defaultTheme
		: defaultTheme;
	
	const { subscribe, set, update } = writable<Theme>(initialTheme);
	
	return {
		subscribe,
		set: (theme: Theme) => {
			if (browser) {
				localStorage.setItem('theme', theme);
				updateDocumentClass(theme);
			}
			set(theme);
		},
		toggle: () => {
			update(theme => {
				const newTheme = theme === 'light' ? 'dark' : 'light';
				if (browser) {
					localStorage.setItem('theme', newTheme);
					updateDocumentClass(newTheme);
				}
				return newTheme;
			});
		},
		init: () => {
			if (browser) {
				updateDocumentClass(initialTheme);
			}
		}
	};
}

function updateDocumentClass(theme: Theme) {
	if (browser) {
		const html = document.documentElement;
		html.classList.remove('light', 'dark');
		html.classList.add(theme);
	}
}

export const themeStore = createThemeStore();