import os
from unittest.mock import patch
from aigent.agent import build_agent


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test", "TAVILY_API_KEY": "tvly-test"})
def test_build_agent_returns_compiled_graph():
    agent = build_agent()
    # Verify it's a compiled LangGraph with expected nodes
    assert hasattr(agent, "invoke")
    assert hasattr(agent, "ainvoke")
    assert hasattr(agent, "get_state")
