你现在位于 VS Code 工作区 videomind-agent。

我要开发一个项目：VideoMind Agent。

项目定位：
基于 FastAPI + LangGraph 的视频学习内容消化 Agent。
支持文本/视频输入，自动完成字幕提取、Whisper 兜底转写、长文本总结、关键词解释、复习题生成、思维导图生成和 trace 日志记录。

目标岗位：
北京非算法方向的大模型应用开发实习、AI Agent 开发实习、Python AI 后端实习。

请严格遵守以下开发原则：

1. 不要一次性实现所有功能。
2. 代码必须分层清晰，方便维护。
3. api 只放路由。
4. core 放 LLM、异常、日志等基础能力。
5. services 放业务逻辑。
6. tools 放具体工具能力。
7. graph 放 LangGraph 工作流。
8. skills 放 prompt 技能文件，不要把大段 prompt 写死在 Python 代码里。
9. storage 放运行产生的 transcript、compressed、outputs、traces。
10. mcp 目录先预留，第一阶段不实现真正 MCP Server。
11. 每个阶段完成后，告诉我修改了哪些文件、如何运行、如何验收。
12. 不要删除我已有的文件，除非明确说明原因。
13. 不要使用复杂数据库，第一版用本地 JSON 文件保存 trace 和输出。
14. 代码要有基础异常处理。
15. 先保证项目能跑，再考虑高级优化。

最终项目目录希望接近：

videomind-agent/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── api/
│   ├── core/
│   ├── graph/
│   ├── services/
│   ├── tools/
│   ├── skills/
│   ├── mcp/
│   ├── storage/
│   └── utils/
├── frontend/
├── eval/
├── docs/
└── tests/

现在先不要写代码，只回复你理解的项目开发原则和接下来建议的第一步。