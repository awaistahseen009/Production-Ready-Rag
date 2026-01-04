from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    convert_to_messages,
)

SYSTEM_PROMPT = """
Use the context below to answer.
If unknown, say you don't know.

Context:
{context}
"""

llm = ChatOpenAI(model="gpt-4o-mini")

def run_rag(question, history, retriever):
    docs = retriever.invoke(question)
    print(f"DOCS LENGTH: {len(docs)}")
    context = "\n\n".join(d.page_content for d in docs)
    docs = [d.page_content for d in docs]
    messages = [SystemMessage(content=SYSTEM_PROMPT.format(context=context))]
    messages.extend(convert_to_messages(history))
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)
    return response.content, docs
