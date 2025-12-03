from typing import Any
from ..configs import config

def get_llm() -> Any:
    """
    Return a LangChain ChatGroq LLM if GROQ_API_KEY is available,
    otherwise fall back to a very simple stub LLM for local testing.
    """
    groq_api_key = config.groq_api_key
    if groq_api_key:
        try:
            from langchain_groq import ChatGroq

            model = config.groq_model
            return ChatGroq(api_key=groq_api_key, model=model, temperature=0.2)
        except Exception:
            # Fall through to stub
            pass

    class StubLLM:
        def invoke(self, prompt: Any) -> Any:
            return "Stub summary: forecast generated. (GROQ_API_KEY not set)"

    return StubLLM()


