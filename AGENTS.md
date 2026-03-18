# Repository Guidelines

## Project Structure & Module Organization
This repository is a Jekyll blog published with GitHub Pages. Posts live in [`_posts/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/_posts) and must use the `YYYY-MM-DD-title.md` naming pattern. Layouts and shared partials are in [`_layouts/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/_layouts) and [`_includes/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/_includes). Site settings, domain, and social metadata live in [`_config.yml`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/_config.yml) and [`CNAME`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/CNAME). Editable style sources are in [`less/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/less), with generated assets committed under [`css/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/css). Long-form personal notes are under [`记录/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/记录); treat them as source material, not automatically publishable content.

## Build, Test, and Development Commands
Use Jekyll for site generation and the local Node tools only for asset rebuilds.

- `bundle exec jekyll serve --livereload`: run the blog locally.
- `bundle exec jekyll build`: generate the production site into `_site/`.
- `./node_modules/.bin/lessc less/hux-blog.less css/hux-blog.css`: rebuild the main stylesheet.
- `./node_modules/.bin/cleancss -o css/hux-blog.min.css css/hux-blog.css`: regenerate the minified stylesheet.

If you change `less/`, update both committed CSS outputs.

## Coding Style & Naming Conventions
Preserve the existing style in each file and avoid broad reformatting. Keep YAML front matter on every post and page. For content work, prefer concise titles, meaningful subtitles, and a small tag set. Publish only from reviewed material in [`记录/整理版/`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/记录/整理版) rather than raw notes.

## Testing Guidelines
There is no dedicated automated test suite. Validate changes with `bundle exec jekyll build`, then review at least the home page, one post page, the tags page, and the custom domain navigation paths. For visual changes, also confirm desktop and mobile layouts.

## Commit & Pull Request Guidelines
Use short imperative commit messages such as `Publish AAC intro post` or `Refresh home page layout`. Keep content, styling, and config changes logically separated when practical. PRs should call out domain or Pages changes, include screenshots for UI updates, and mention whether generated CSS was rebuilt.

## Security & Configuration Tips
Treat [`_config.yml`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/_config.yml) and [`CNAME`](/Users/yvain/yvain_personal/github_blog/YvainZhang.github.io/CNAME) as deployment-critical files. Do not publish raw notes that contain customer, internal network, server, or credential details. When reusing this repo, replace usernames, analytics IDs, and domain settings before publishing.
