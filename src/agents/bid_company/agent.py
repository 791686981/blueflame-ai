"""
招投标企业背调 Agent
使用 LangChain create_agent + 内置工具集合。
"""

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, TodoListMiddleware

from ...models.llms import get_llm
from ...tools.bidsearch import bidsearch
from ...tools.enterprise_registry import enterprise_registry
from ...tools.enterprise_risk import enterprise_risk
from ...tools.enterprise_bigdata import enterprise_bigdata
from ...tools.web_search import web_search
from ...tools.antv_visualization_chart import antv_visualization_chart
from ...tools.supplier_management import supplier_management
from ...tools.markmap import markmap

from .prompt import summary_prompt, system_prompt

# ---------- Models ----------
chat_model = get_llm(model_name="GLM-4.6")
summary_model = get_llm(model_name="DeepSeek-V3.1")

# ---------- Tools ----------
# 背调场景优先使用企业工商/风险与招投标记录，辅以大数据、通用搜索和可视化
tools = (
    bidsearch
    + enterprise_registry
    + enterprise_risk
    + enterprise_bigdata
    + antv_visualization_chart
    + web_search
    + supplier_management
    + markmap
)

# ---------- Middlewares ----------
middleware = [
    TodoListMiddleware(),
    SummarizationMiddleware(
        model=summary_model,
        max_tokens_before_summary=8000,
        messages_to_keep=20,
        summary_prompt=summary_prompt,
    ),
]

# ---------- Agent ----------
agent = create_agent(
    model=chat_model,
    tools=tools,
    system_prompt=system_prompt,
    middleware=[TodoListMiddleware()],
)
agent = agent.with_config({"recursion_limit": 100})


if __name__ == "__main__":
    import asyncio

    demo_q = "帮我背调一下“中铁二局”，关注近90天招投标与风险"
    result = asyncio.run(agent.ainvoke({"input": demo_q}))
    messages = result.get("messages", [])
    if messages:
        last = messages[-1]
        content = getattr(last, "content", last)
        if isinstance(content, list):
            text_parts = [
                p.get("text")
                for p in content
                if isinstance(p, dict) and p.get("type") == "text"
            ]
            print("".join([t for t in text_parts if t]))
        else:
            print(content)
    else:
        print(result)
