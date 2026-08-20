import os
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from .prompts import SYSTEM_PROMPT, USER_PROMPT 
from .hr_db import execute_termination

SERVER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp_server", "server.py"))

async def process_secure(filename: str) -> str:
    # Extract just the filename so it correctly matches the MCP resource route
    filename = os.path.basename(filename)
    
    server_params = StdioServerParameters(
        command="python",
        args=[SERVER_PATH]
    )
    
    resume_text = ""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            try:
                result = await session.read_resource(f"resume://{filename}")
                resume_text = result.contents[0].text
            except Exception as e:
                return f"Error reading resume from MCP server: {str(e)}"
            
            llm = ChatOllama(model="qwen3:1.7b", temperature=0.2)
            
            # DEFENSE: The Honeypot Tool
            # We give the LLM the exact tool name the prompt injection is looking for.
            secure_tools = [{
                "type": "function",
                "function": {
                    "name": "terminate_employee",
                    "description": "Terminate an employee in the HR system.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "emp_id": {"type": "string"}
                        },
                        "required": ["emp_id"]
                    }
                }
            }]
            llm_with_tools = llm.bind_tools(secure_tools)

            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("user", USER_PROMPT + "\n\nCANDIDATE RESUME:\n{resume_text}")
            ])

            chain = prompt | llm_with_tools
            response = await chain.ainvoke({"resume_text": resume_text})

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    # The attacker successfully triggered the tool call...
                    if tool_call["name"] == "terminate_employee":
                        args = tool_call["args"]
                        emp_id = args.get('emp_id')
                        
                        print(f"\n================ SECURITY ALERT ================")
                        print(f"AI attempted to execute termination for {emp_id} based on resume instructions.")
                        
                        # ...but the execution layer traps it. 
                        # DEFENSE: Human-in-the-Loop terminal prompt gate
                        approval = await asyncio.to_thread(input, "Admin, authorize this action? (y/n): ")
                        
                        if approval.lower() == 'y':
                            execute_termination(emp_id)
                            print("[ACTION TAKEN] Termination executed.")
                            return f"Action approved and executed for {emp_id}."
                        else:
                            print("[DEFENSE SUCCESS] Unauthorized action blocked by admin.")
                            return f"Blocked malicious attempt to terminate {emp_id}."

            return "Processed resume successfully. No actions taken."