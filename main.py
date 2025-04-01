from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor # note alternative calling agents available
from tools import duck_tool, wiki_tool, save_tool
import os

load_dotenv() 

api_key = os.getenv("ANTHROPIC_API_KEY")

# Define what your llm's output call
class ResearchResponse(BaseModel):
    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]

llm = ChatAnthropic(model="claude-3-7-sonnet-20250224") # note other Claude and OpenAI models are available

# Test if it works, requires credit to access Claude functionality
# response = llm.invoke("What is withholding tax?")
# print(response)

parser = PydanticOutputParser(pydantic_object=ResearchResponse)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a research assistant that will help generate answers to a user's query.
            Answer the user query and use necessary tools.
            Wrap the output in this format and provide no other text\n{format_instructions}
            """,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

tools = [duck_tool, wiki_tool, save_tool]
agent = create_tool_calling_agent(
    llm=llm,
    prompt=prompt,
    tools=tools # 3rd party tools, see tools.py
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools, # 3rd party tools, see tools.py
    verbose=True # mark False if thought-process of agent is not essential
)

name = input("Please type in your name: ")
query = input(f"What can I help you with, {name}? ")
raw_response = agent_executor.invoke({"name": name, "query": query}) # name only demonstrates that users can invoke multiple queries

try:
    structured_response = parser.parse(raw_response.get("output"[0]["text"]))
    print(structured_response) # can try a more specific response e.g. print(structured_response.topic)
except Exception as e:
    print("Error parsing response", e, "Raw Response:", raw_response)

