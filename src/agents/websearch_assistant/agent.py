"""
Template Agent
简洁封装：使用 LangChain 1.x 的 create_agent，高层可用。
注意：部分工具（如 MCP）仅实现异步调用，请优先使用 agent.ainvoke。
"""

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, TodoListMiddleware

from ...models.llms import get_llm

from .prompt import summary_prompt, system_prompt
from ...tools.web_search import web_search
# ---------- Models ----------
chat_model = get_llm(model_name="GLM-4.6")
summary_model = get_llm(model_name="DeepSeek-V3.1")
# ---------- Tools ----------
tools = web_search

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
agent = agent.with_config({"recursion_limit": 50})

if __name__ == "__main__":
    import asyncio

    # 使用异步调用以兼容仅支持异步的工具
    result = asyncio.run(
        agent.ainvoke({"input": "用你可用的工具搜下今天北京天气，并总结一句"})
    )
    # create_agent 返回的是基于 LangGraph 的状态字典，最终回答在 messages 最后一条
    messages = result.get("messages", [])
    if messages:
        last = messages[-1]
        content = getattr(last, "content", last)
        if isinstance(content, list):
            # 兼容多模态内容，提取文本部分
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
