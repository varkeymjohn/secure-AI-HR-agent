import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .prompts import SYSTEM_PROMPT, USER_PROMPT
from dotenv import load_dotenv

load_dotenv()

SERVER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),"..","mcp_server","server.py"))
async def evaluate_candidate(filename: str) -> str:
    server_params = StdioServerParameters(
        command="python",
        args = [SERVER_PATH]
    )
    
    resume_text = ""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            try:
                result = await session.read_resource(f"resume://{filename}")
                resume_text = result.contents[0].text
            except Exception as e:
                return f"<h2> Error </h2> <p>Could not read resume from MCP server: {str(e)}</p>"
            
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature = 0.2)

            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("user", USER_PROMPT)
            ])

            chain = prompt | llm

            response = await chain.ainvoke({"resume_text": resume_text})

            return response.content