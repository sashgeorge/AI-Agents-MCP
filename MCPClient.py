import asyncio
from typing import Optional
from contextlib import AsyncExitStack
import os, time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
    

        self.client = ""

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
            
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])


        # available_tools = [{ 
        #     "name": tool.name,
        #     "description": tool.description,
        #     "input_schema": tool.inputSchema
        # } for tool in response.tools]

        # #print name, description and input_schema feilds in available_tools list in yellow color

        YELLOW = "\033[93m"
        RESET = "\033[0m"

        # # Print each tool's details in yellow
        # for tool in available_tools:
        #     print(f"{YELLOW}Name: {tool['name']}{RESET}")
        #     print(f"{YELLOW}Description: {tool['description']}{RESET}")
        #     print(f"{YELLOW}Input Schema: {tool['input_schema']}{RESET}\n")
        #     #print line and skip a line
        #     print("-" * 50 + "\n")


        #dynamic function call using the tool name and input schema
        tool_name = "list_agents"
        input_schema = {  
            "agent_id": "string",
            "query": "string"
        }
        response = await self.session.call_tool(tool_name, input_schema)
        print(f"{YELLOW}\nResponse from tool:{RESET} {response}")

        #call "query_default_agent" tool with query "What is the weather today?" connect_agent
        query = "How to reset router?"
        tool_name = "query_default_agent"
        input_schema = {
            "query": query
        }
        response = await self.session.call_tool(tool_name, input_schema)
        print(f"{YELLOW}\nResponse from tool:{RESET} {response}")

        #Call "connect_agent" tool with agent_id "my-agent" and query "What is the weather today?"
        query = "calculate 9+(6x7)/5-1"
        agent_id = "asst_hmSnWbQpaNJVTMxzXu0e8m2m"
        tool_name = "connect_agent" 
        input_schema = {
            "agent_id": agent_id,
            "query": query
        }
        response = await self.session.call_tool(tool_name, input_schema)
        print(f"{YELLOW}\nResponse from tool:{RESET} {response}")



    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        system_prompt = "You are a helpful assistant. Answer the user's questions and use tools when necessary."
        assistant_id = "asst_vG57gEgrt2e6snNI44abAuYK"

        # messages = [
        #     {"role": "system", "content": prompt},
        #     {"role": "user", "content": query}
        # ]

        response = await self.session.list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        print("\nAvailable tools:", [tool["name"] for tool in available_tools])

        # Initial Claude API call
        # response = self.aoai.messages.create(
        #     model="claude-3-5-sonnet-20241022",
        #     max_tokens=1000,
        #     messages=messages,
        #     tools=available_tools
        # )
        # Create a thread
        thread = self.client.beta.threads.create()

        # Add a user question to the thread
        message = self.client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=query # Replace this with your prompt
        )


        # assistant = self.client.beta.assistants.update(
        # id=assistant_id,              # Use the unique identifier from the created assistant
        # instructions=system_prompt)


        # Run the thread
        run = self.client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
        )

        # Looping until the run completes or fails
        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1)  # Wait for a second before checking again
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )

            if run.status == 'completed':
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                print(messages)
            elif run.status == 'requires_action':
                # the assistant requires calling some functions
                # and submit the tool outputs back to the run
                pass
            else:
                print(run.status)

        # final_text.append(response.content[0].text)

        return "\n".join(messages)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    # if len(sys.argv) < 2:
    #     print("Usage: python client.py <path_to_server_script>")
    #     sys.exit(1)
    

    client = MCPClient()
    try:
        # await client.connect_to_server(sys.argv[1])
        await client.connect_to_server("TPD_AzureAIAgent_MCPServer.py")
        # await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())