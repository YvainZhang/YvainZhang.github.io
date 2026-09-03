# 文档站使用说明

建议在独立 Python 虚拟环境中运行：

```bash
python3 -m venv .venv-docs
. .venv-docs/bin/activate
pip install -r requirements-docs.txt
mkdocs serve
```

浏览器访问终端显示的本地地址。静态构建使用 `mkdocs build --strict`，默认输出到仓库根目录的 `SoC-site`，避免生成物混入 Markdown 源文件。Mermaid 由 `mkdocs-mermaid2-plugin` 渲染。

线上站点由 GitHub Pages 工作流组合构建：先把 Jekyll 博客生成到 `_site`，再把本知识库生成到 `_site/tech/soc`，最后统一发布。因此公开地址是 `/tech/soc/`，不要把 MkDocs 产物直接提交到仓库。
