from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def generate_chat_title(question: str) -> str:
    prompt = f"Generate a short descriptive title (max 6 words) for this question:\n{question}"
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip().strip('"')

