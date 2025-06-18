"""Application entry point."""
from lets_talk.api.main import app
from lets_talk.agents.react_agent import default_agent 

reat_agent = default_agent.agent

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
