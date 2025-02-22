from stuart.settings import settings
from langfuse.openai import openai

def _check_models(model_name: str, api_key: str, base_url: str = None):
    """Checks if the model exists in the client's model list."""
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    models = client.models.list()
    if any(model.id == model_name for model in models):
        return client
    return None

def create_client(model_name: str):
    """Creates a client based on the model name."""
    if settings.openai_api_key:
        client = _check_models(model_name, settings.openai_api_key)
        if client:
            return client

    if settings.together_api_key:
        client = _check_models(model_name, settings.together_api_key, base_url="https://api.together.xyz/v1")
        if client:
            return client

    raise ValueError(f"Model {model_name} not found in either OpenAI or TogetherAI")

REASONING_CLIENT = create_client(settings.reasoning_client_model)
CODING_CLIENT = create_client(settings.coding_client_model)
