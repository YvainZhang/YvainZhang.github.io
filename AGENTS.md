# Repository Guidelines

## Project Structure & Module Organization
This repository is a Jekyll blog for GitHub Pages. Content lives in [`_posts/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/_posts), with dated Markdown filenames such as `2021-03-29-KVO详解.md`. Shared templates are in [`_layouts/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/_layouts) and [`_includes/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/_includes). Site configuration is in [`_config.yml`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/_config.yml). Static assets are committed under [`css/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/css), [`js/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/js), [`img/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/img), [`fonts/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/fonts), and [`pwa/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/pwa). LESS sources live in [`less/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/less).

## Build, Test, and Development Commands
Use Jekyll for site generation and Grunt only for asset rebuilds.

- `jekyll serve -w`: build and preview the site locally with live reload.
- `jekyll build`: generate the production site into `_site/`.
- `grunt`: compile LESS and minify JS based on [`Gruntfile.js`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/Gruntfile.js).
- `grunt watch`: rebuild CSS/JS when files in `less/` or `js/` change.

The npm scripts in [`package.json`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/package.json) are legacy and currently inconsistent with the committed asset names, so prefer the direct commands above.

## Coding Style & Naming Conventions
Preserve the existing style in each file: 4-space indentation in HTML, JS, and config files; no unnecessary reformatting. Keep post filenames in Jekyll format: `YYYY-MM-DD-title.md`. Use YAML front matter for every post and page. Edit source files in `less/` and unminified files in `js/`; commit generated assets in `css/` and minified JS only when they change with the source.

## Testing Guidelines
There is no dedicated automated test suite in this repository. Validation is done by running `jekyll build` and reviewing the local site with `jekyll serve -w`. For UI changes, verify at least the home page, one post page, the tags page, and mobile navigation behavior.

## Commit & Pull Request Guidelines
Recent history includes short messages like `delete file`, but contributors should use clear imperative summaries such as `Add post about Swift concurrency` or `Fix broken sidebar link`. Keep commits focused. Pull requests should include a brief description, affected pages or templates, screenshots for visual changes, and any config changes in `_config.yml`.

## Security & Configuration Tips
Treat [`_config.yml`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/_config.yml) as the source of truth for site metadata and third-party integrations. When forking or reusing this repo, replace external service credentials, usernames, and analytics identifiers before publishing.
