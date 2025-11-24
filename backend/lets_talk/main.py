"""Application entry point."""




from lets_talk.api.main import app
from lets_talk.agents.react_agent import ReactAgent
from lets_talk.agents.rag_agent import RAGAgent


react_agent = ReactAgent().agent
rag_agent = RAGAgent().graph


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
