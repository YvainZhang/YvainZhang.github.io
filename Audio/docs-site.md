# 文档站使用说明

建议在独立 Python 虚拟环境中运行：

```bash
python3 -m venv /tmp/yvain-audio-docs-env
. /tmp/yvain-audio-docs-env/bin/activate
pip install -r Audio/requirements-docs.txt
mkdocs serve --config-file Audio/mkdocs.yml
```

以上命令从博客仓库根目录执行。浏览器访问终端显示的本地地址。静态构建使用 `mkdocs build --strict --config-file Audio/mkdocs.yml`，默认输出到根目录下的 `Audio-site`，避免生成物混入 Markdown。Mermaid 使用与其他专题一致的自定义代码块渲染；公式使用 arithmatex 与 MathJax。

单独预览时，顶部 `/` 和 `/tech/` 需要完整博客服务器才能验证。组合预览应先 `bundle exec jekyll build`，再 `mkdocs build --strict --config-file Audio/mkdocs.yml --site-dir _site/tech/audio`，最后 `python3 -m http.server 8000 --directory _site`，访问 `http://localhost:8000/tech/audio/`。其他专题须分别构建，后续不要再执行 Jekyll 覆盖组合产物。

线上站点由 GitHub Pages 工作流组合构建：先把 Jekyll 博客生成到 `_site`，再把本知识库生成到 `_site/tech/audio`，最后统一发布。因此公开地址是 `/tech/audio/`，不要把 MkDocs 产物直接提交到仓库。

## 环境迁移

虚拟环境包含绝对解释器路径，不应跨机器复制。仓库忽略所有 `.venv-docs/` 与 `.venv/`，MkDocs 也排除这些目录。已有本地环境可以保留，但不要修补其中的 shebang 后假定全部依赖可迁移；在独立目录重新创建并安装依赖。

使用 `python -m mkdocs --version` 检查当前激活环境，使用 `git check-ignore Audio/.venv-docs/bin/mkdocs` 检查忽略规则。本文安装范围尚未锁定全部传递依赖，严格复现实验时应另外保存 Python 版本和依赖清单。

本轮在全新独立环境验证的核心版本：Python 3.9、MkDocs 1.6.1、Material 9.7.7、mermaid2 1.2.3。现有旧环境未删除，也不参与验证。
