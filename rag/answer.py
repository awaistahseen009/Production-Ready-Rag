from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, convert_to_messages
import os
load_dotenv(override=True)
from langchain_core.prompts import ChatPromptTemplate

current_dir = os.path.dirname(os.path.abspath(__file__))
PERSISTANT_DIR = os.path.join(current_dir, "db", "chroma_files")
embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )
retriever = Chroma(persist_directory=PERSISTANT_DIR, embedding_function=embeddings).as_retriever()
messages = [
    ("system","You are an helpful assistant and given the context give the answer of the questions: {context}"), 
    ("user", "{question}")
]
prompt = ChatPromptTemplate.from_messages(messages)
llm = ChatOpenAI(model = "gpt-4o-mini")
RETRIEVAL_K = 10


SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant .
You are chatting with a user about research papers.
If relevant, use the given context to answer any question.
If you don't know the answer and couldnt find any context, say so.
Context:
{context}
"""




def combined_question(question: str, history: list[dict] = []) -> str:
    """
    Combine all the user's messages into a single string.
    """
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")
    return prior + "\n" + question

def fetch_context(question: str) -> list[Document]:
    """
    Retrieve relevant context documents for a question.
    """
    return retriever.invoke(question, k=RETRIEVAL_K)

def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    """
    Answer the given question with RAG; return the answer and the context documents.
    """
    combined = combined_question(question, history)
    docs = fetch_context(combined)
    context = "\n\n".join(doc.page_content for doc in docs)
    system_prompt = SYSTEM_PROMPT.format(context=context)
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history))
    messages.append(HumanMessage(content=question))
    response = llm.invoke(messages)
    return response.content, docs

if __name__=="__main__":
    question = "Whos awais tahseen ?"
    context = " ".join([doc.page_content for doc in retriever.invoke(question)])
    # print(context)

    chain = prompt|llm | StrOutputParser()
    print(chain.invoke({"context": context,"question":question }))