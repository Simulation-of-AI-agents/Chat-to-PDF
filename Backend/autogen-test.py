from autogen import AssistantAgent, UserProxyAgent
from autogen import ConversableAgent

api_key =  "sk-proj-hbUXw7vKgWslYPGb8W3WT3BlbkFJervoSdFmAh0KKQ8z3RWH",

config_list = [
  {
    "model": "gemma:2b",
    "api_key": "ollama",
  }
]

assistant = AssistantAgent("assistant", llm_config={"config_list": config_list})

user_proxy = UserProxyAgent("user_proxy", code_execution_config=False)
user_proxy.initiate_chat(assistant, message="What is Python (Programming Language)")
