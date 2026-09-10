# 文档站使用说明

建议在独立 Python 虚拟环境中运行：

```bash
python3 -m venv .venv-docs
. .venv-docs/bin/activate
pip install -r requirements-docs.txt
mkdocs serve
```

浏览器访问终端显示的本地地址。静态构建使用 `mkdocs build --strict`，默认输出到仓库上层目录的 `RTOS-site` (../RTOS-site)，避免生成物混入 Markdown 源文件。Mermaid 由 `mkdocs-mermaid2-plugin` 渲染。
