# Yvain Zhang Blog

This repository hosts the Jekyll-based GitHub Pages site for `YvainZhang.github.io`.

## Local development

Install Ruby gems and Node dependencies:

```bash
bundle install --path vendor/bundle
npm install
```

`github-pages` now expects a modern Ruby runtime. If your machine still uses the system Ruby 2.6.x, install Ruby 3.x first, then run `bundle install`.

Run the site locally:

```bash
bundle exec jekyll serve --livereload
```

Rebuild frontend assets when editing files in `less/` or `js/`:

```bash
npm run build:assets
npm run watch:assets
```

## Content structure

- `_posts/`: blog posts with filenames like `YYYY-MM-DD-title.md`
- `_layouts/`, `_includes/`: shared Jekyll templates
- `less/`: stylesheet sources compiled into `css/`
- `js/`: unminified scripts; commit minified output when source changes
- `_config.yml`: site metadata and plugin configuration

## Deployment

Use GitHub Pages built-in Jekyll publishing from the repository root.

On GitHub:

1. Open `Settings > Pages`.
2. Set `Source` to `Deploy from a branch`.
3. Set `Branch` to `master` and folder to `/ (root)`.
4. Save and wait for GitHub Pages to finish building.

## Notes

- This is a user site repository, so the published URL is `https://YvainZhang.github.io/`.
- After changing `_config.yml`, run `bundle exec jekyll build` locally to catch config errors early.
