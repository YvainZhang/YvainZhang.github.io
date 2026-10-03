# SoC 发布快照

博客中的 `SoC/` 是独立 SoC 仓库的发布快照，不包含其 `.git` 目录或提交历史。默认源仓库位于博客同级目录 `../SoC`。

## 更新步骤

先在独立仓库中提交内容，再从博客根目录运行：

```bash
./_scripts/sync-soc.sh
```

脚本只导出源仓库当前 `HEAD` 中已提交的文件；如果源仓库存在未提交修改，脚本会停止。同步完成后，`SoC/.source-commit` 会记录来源提交。

博客专用首页、主题覆盖、前端资源和部分文章的文案修订保存在 `overlay/`，每次同步后自动覆盖到快照。文章覆盖文件使用与 `SoC/` 相同的相对路径；修改这些文章时，应同时更新快照与覆盖文件。若源仓库更新了同名文章，需要先将新内容合并到覆盖文件，避免同步后被旧内容覆盖。

`mkdocs.yml` 继承源仓库配置，只覆盖博客域名和主题设置，因此源仓库新增的导航项会自动进入发布站点。

提交前运行与 GitHub Pages 相同的构建检查：

```bash
bundle exec jekyll build --destination _site
mkdocs build --strict --config-file _soc_publish/mkdocs.yml \
  --site-dir "$PWD/_site/tech/soc"
```

确认后，将 `SoC/`、`_soc_publish/`、`_scripts/sync-soc.sh` 一并提交到博客仓库。
