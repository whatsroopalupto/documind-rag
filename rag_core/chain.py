from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
import os
from dotenv import load_dotenv

load_dotenv()

def create_conversation_chain(vectorstore):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
        memory=memory,
        return_source_documents=True,
        verbose=False
    )

    return chain


def get_answer(chain, question):
    result = chain.invoke({"question": question})
    answer = result["answer"]

    sources = []
    for doc in result["source_documents"]:
        source_info = {
            "page": doc.metadata.get("page", 0),
            "file": doc.metadata.get("source", "Unknown file"),
            "line": doc.metadata.get("start_line", 1),
            "preview": doc.metadata.get("preview", "")
        }
        sources.append(source_info)

    return answer, sources