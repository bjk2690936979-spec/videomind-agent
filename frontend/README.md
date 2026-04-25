# VideoMind Agent Frontend

这是 VideoMind Agent 的 Streamlit 演示页面，用于快速体验文本和视频链接学习内容生成。

## 启动方式

先启动后端：

```bash
uvicorn backend.main:app --reload
```

再启动前端：

```bash
streamlit run frontend/app.py
```

默认前端地址：

```text
http://localhost:8501
```

## 后端地址配置

页面侧边栏可以修改后端地址，默认是：

```text
http://127.0.0.1:8000
```

## 页面功能

- 文本学习内容生成
- 视频链接学习内容生成
- trace_id 展示
- Trace 查询
- Mermaid mindmap 文本展示

## 当前限制

第一版不渲染 Mermaid 图形，只展示 Mermaid 文本。
