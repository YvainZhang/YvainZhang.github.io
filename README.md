# Yvain Zhang Blog

This repository hosts the Jekyll-based GitHub Pages site for `YvainZhang.github.io`, including the SoC and Wi-Fi system knowledge collections.

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

Build the two system knowledge collections into the combined site:

```bash
mkdocs build --strict --config-file _soc_publish/mkdocs.yml --site-dir "$PWD/_site/tech/soc"
mkdocs build --strict --config-file WiFi/mkdocs.yml --site-dir "$PWD/_site/tech/wifi"
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
- `SoC/`, `WiFi/`: MkDocs-based system knowledge collections
- `_config.yml`: site metadata and plugin configuration

## Deployment

The GitHub Actions Pages workflow builds Jekyll together with both MkDocs collections.

On GitHub:

1. Open `Settings > Pages`.
2. Set `Source` to `GitHub Actions`.
3. Push to `master` or manually run the Pages workflow.

## Notes

- This is a user site repository, so the published URL is `https://YvainZhang.github.io/`.
- After changing `_config.yml`, run `bundle exec jekyll build` locally to catch config errors early.
