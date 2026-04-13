import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://caregraph.org',
  output: 'static',
  build: {
    format: 'directory',
  },
});
