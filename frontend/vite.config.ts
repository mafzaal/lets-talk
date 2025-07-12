import devtoolsJson from 'vite-plugin-devtools-json';
import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit(), devtoolsJson()],
	// server: {
	// 	proxy: {
	// 		// Proxy API requests to backend during development
	// 		'/api': {
	// 			target: 'http://localhost:8000',
	// 			changeOrigin: true,
	// 			rewrite: (path) => path.replace(/^\/api/, '/api'),
	// 		},
	// 	},
	// },
});
