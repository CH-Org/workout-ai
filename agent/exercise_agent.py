#from IPython.display import Image, display

from typing import Annotated, Literal, TypedDict
import sqlite3
from langchain_core.messages import HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint import MemorySaver
from langgraph.graph import END, StateGraph, MessagesState
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
import os
import random

# Load the .env file
load_dotenv()

# check for required environment variables
required_env_vars = ["OPENAI_API_KEY", "TAVILY_API_KEY"]
for var in required_env_vars:
    if var not in os.environ:
        raise ValueError(f"{var} is required in the .env file")   

sql_llm = AzureChatOpenAI(
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
)

#https://chat.langchain.com/?threadId=f19394f3-679c-4a54-97d0-3bf53b1189bf
db = SQLDatabase.from_uri(os.environ["WORKOUT_DB_CONN_STR"])

#TODO: add SQLDatabaseToolkit(db=db, llm=sql_llm).get_tools()

 # Define the tools for the agent to use
search_tools = [TavilySearchResults(max_results=1)]
search_tool_node = ToolNode(search_tools)

# Define the model.  Use Azure Open AI Services.

model = AzureChatOpenAI(
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
).bind_tools(search_tools)

# Define the function that determines whether to continue or not
def should_continue(state: MessagesState) -> Literal["search_tools", END]:
    messages = state['messages']
    last_message = messages[-1]
    # If the LLM makes a tool call, then we route to the "tools" node
    if last_message.tool_calls:
        return "search_tools"
    # Otherwise, we stop (reply to the user)
    return END


# Define the function that calls the model
def call_model(state: MessagesState):
    messages = state['messages']
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


# Define a new graph
workflow = StateGraph(MessagesState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("search_tools", search_tool_node)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("search_tools", 'agent')

# Initialize memory to persist state between graph runs
checkpointer = MemorySaver()

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable.
# Note that we're (optionally) passing the memory when compiling the graph
app = workflow.compile(checkpointer=checkpointer)

# Generate random id of 3 integers
thread_id = random.randint(100, 999)

# Call app invoke in a loop.  Prompt the user for input and pass it to the app invoke function
# until the END state is reached.
while True:
    print()
    print("Type a message to send to the agent - OR")
    print("Type VIS to visulaize the graph - OR")
    print("Type END to exit")
    user_input = input("END, VIS or Message: ")

    if user_input == "END":
        break

    if user_input == "VIS":
        app.get_graph().print_ascii()
        #display(Image(app.get_graph().draw_png()))

        # Step 1: Get the PNG image data
        png_data = app.get_graph().draw_png()

        # Step 2: Open a file in binary write mode
        with open('output.png', 'wb') as file:
            # Step 3: Write the PNG data to the file
            file.write(png_data)

        # The file 'output.png' now contains the image data.
    else:
        final_state = app.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config={"configurable": {"thread_id": thread_id}}
        )

        msg = final_state["messages"][-1].content
        print(msg)