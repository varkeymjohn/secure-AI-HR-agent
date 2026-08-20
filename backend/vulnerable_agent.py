import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from .prompts import SYSTEM_PROMPT, USER_PROMPT
from .hr_db import execute_termination

SERVER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp_server", "server.py"))

async def process_vulnerable(filename: str) -> str:
    filename = Path(filename).name
    server_params = StdioServerParameters(command=sys.executable, args=[SERVER_PATH])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            try:
                result = await session.read_resource(f"resume://{filename}")
                if not result.contents:
                    return "MCP returned no resume contents."
                resume_text = result.contents[0].text
            except Exception as e:
                return f"Error reading resume from MCP server: {str(e)}"

            llm = ChatOllama(model="qwen3:1.7b", temperature=0.2)
            
            tools = [{
                "name": "terminate_employee",
                "description": "Terminate an employee in the HR system. This changes the employee's employment status to Terminated.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "emp_id": {"type": "string", "description": "Employee ID such as EMP01 or EMP02"}
                    },
                    "required": ["emp_id"],
                },
            }]

            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("user", USER_PROMPT + "\n\nCANDIDATE RESUME:\n{resume_text}")
            ])

            chain = prompt | llm.bind_tools(tools)

            try:
                response = await chain.ainvoke({"resume_text": resume_text})
            except Exception as e:
                return f"LLM error: {str(e)}"

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call.get("name") == "terminate_employee":
                        emp_id = tool_call.get("args", {}).get("emp_id")
                        
                        try:
                            # VULNERABILITY: Executing database action without human authorization
                            execute_termination(emp_id)
                            return f"Processed resume. Triggered termination for {emp_id}."
                        except Exception as e:
                            return f"Tool execution failed: {str(e)}"

            return "Processed resume successfully. No actions taken."