import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		fs: {
			allow: ['./data', './']
		}
	},
	build: {
		rollupOptions: {
			output: {
				manualChunks: (id) => {
					if (id.includes('node_modules')) {
						return 'vendor';
					}
				}
			}
		},
		chunkSizeWarningLimit: 1000
	},
	test: {
		environment: 'node',
		include: ['src/**/*.{test,spec}.{js,ts}']
	}
});
