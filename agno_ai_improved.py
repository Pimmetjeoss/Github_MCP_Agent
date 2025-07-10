# agno_ai_server.py - Draait AgnoAI als een webserver met FastAPI
import re
import asyncio
import os
import sys
from typing import Dict, Any, Optional
import json
from contextlib import AsyncExitStack, asynccontextmanager # <-- asynccontextmanager toegevoegd

from dotenv import load_dotenv
import google.generativeai as genai

# NIEUW: Importeer FastAPI en Uvicorn voor de webserver
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("❌ MCP bibliotheek niet gevonden. Installeer met: pip install mcp")
    sys.exit(1)

load_dotenv()


class AgnoAI:
    def __init__(self):
        self.github_session: Optional[ClientSession] = None
        self.tools: Dict[str, str] = {}
        self.exit_stack: Optional[AsyncExitStack] = None
        self.connected = False
        self.llm_model = None

    def _configure_llm(self) -> bool:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ Geen GEMINI_API_KEY gevonden in je environment of .env bestand.")
            return False
        
        try:
            genai.configure(api_key=api_key)
            self.llm_model = genai.GenerativeModel('gemini-1.5-flash')
            print("🧠 LLM-brein (Gemini) geconfigureerd.")
            return True
        except Exception as e:
            print(f"❌ Fout bij configureren van LLM: {e}")
            return False

    async def connect_github(self) -> bool:
        try:
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                print("⚠️  Geen GITHUB_TOKEN gevonden in je environment of .env bestand.")
                return False
            
            print("🔄 Verbinden met GitHub MCP server...")
            self.exit_stack = AsyncExitStack()
            
            server_params = StdioServerParameters(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-github"],
                env={**os.environ, "GITHUB_PERSONAL_ACCESS_TOKEN": token}
            )
            
            stdio = stdio_client(server_params)
            read, write = await self.exit_stack.enter_async_context(stdio)
            
            session = ClientSession(read, write)
            self.github_session = await self.exit_stack.enter_async_context(session)
            await self.github_session.initialize()
            
            tools_response = await self.github_session.list_tools()
            if not tools_response or not tools_response.tools:
                print("⚠️  Geen tools gevonden in GitHub MCP server")
                return False
            
            for tool in tools_response.tools:
                self.tools[f"github_{tool.name}"] = tool.name
            
            self.connected = True
            print(f"✅ GitHub verbonden! {len(self.tools)} tools beschikbaar.")
            return True
        except FileNotFoundError:
            print("❌ NPX niet gevonden. Installeer Node.js (met npm) eerst.")
            return False
        except Exception as e:
            print(f"❌ GitHub verbinding mislukt: {type(e).__name__}: {e}")
            return False

    async def process_command(self, command: str) -> str:
        if not self.connected:
            return "❌ Niet verbonden met GitHub."
        if not self.llm_model:
            return "❌ LLM-brein is niet geconfigureerd. Check je GEMINI_API_KEY."

        prompt = f"""
        Jij bent een AI-assistent die gebruikersverzoeken vertaalt naar een specifieke JSON-tool-aanroep.

        ### REGELS
        1.  Je MOET antwoorden met een enkel, valide JSON-object en niets anders.
        2.  De "tool_name" MOET exact overeenkomen met een van de 'BESCHIKBARE TOOLS'. Verzin geen tools.
        3.  De "parameters" MOETEN correct en volledig worden geëxtraheerd uit het verzoek van de gebruiker.

        ### BESCHIKBARE TOOLS
        {', '.join(self.tools.keys())}

        ### TOOL DETAILS EN VOORBEELDEN

        #### Voorbeeld 1: Repositories van de gebruiker opvragen
        - Gebruiker zegt: "lijst mijn repositories" of "toon mijn repo's"
        - Analyse: De tool 'list_repositories' bestaat niet. We MOETEN 'search_repositories' gebruiken met de speciale query 'user:@me'.
        - JSON antwoord: {{"tool_name": "github_search_repositories", "parameters": {{"query": "user:@me fork:true"}}}}

        #### Voorbeeld 2: Zoeken naar publieke repositories
        - Gebruiker zegt: "zoek naar machine learning projecten in python"
        - Analyse: We gebruiken 'search_repositories' en stoppen de zoekterm in de 'query' parameter. We kunnen de zoekopdracht verfijnen met 'language:'.
        - JSON antwoord: {{"tool_name": "github_search_repositories", "parameters": {{"query": "machine learning language:python"}}}}
        
        #### Voorbeeld 3: Een issue aanmaken
        - Gebruiker zegt: "maak een issue aan in de repo 'test-owner/test-repo' met titel 'Bug' en de tekst 'Het werkt niet'."
        - Analyse: We gebruiken 'create_issue' en vullen alle parameters: owner, repo, title, en body.
        - JSON antwoord: {{"tool_name": "github_create_issue", "parameters": {{"owner": "test-owner", "repo": "test-repo", "title": "Bug", "body": "Het werkt niet."}}}}

        ### HET VERZOEK
        Gebruiker: "{command}"

        ### JOUW JSON-ANTWOORD
        """

        try:
            print("🧠 Brein denkt na...")
            response = await self.llm_model.generate_content_async(prompt)
            
            cleaned_response = re.sub(r'```json\s*|\s*```', '', response.text, flags=re.DOTALL).strip()
            action = json.loads(cleaned_response)
            
            tool_key = action.get("tool_name")
            params = action.get("parameters", {})

            if not tool_key:
                return f"❓ {action.get('reason', 'Ik begreep het verzoek niet.')}"
            
            if tool_key not in self.tools:
                available_tools_str = "\n - ".join(self.tools.keys())
                return (f"❌ Brein stelde een ongeldige tool voor: '{tool_key}'.\n\n"
                        f"Beschikbare tools zijn:\n - {available_tools_str}")
            
            real_tool_name = self.tools[tool_key]
            return await self._call_tool_safe(real_tool_name, params)

        except json.JSONDecodeError:
            return f"❌ Fout: Het brein gaf een ongeldig JSON-antwoord.\nAntwoord was: {response.text}"
        except Exception as e:
            return f"❌ Een onverwachte fout met het brein: {e}"

    async def _call_tool_safe(self, tool_name: str, params: Dict[str, Any]) -> str:
        try:
            print(f"🔧 Aanroepen: {tool_name} met {params}")
            result = await self.github_session.call_tool(tool_name, params)
            
            if result.content:
                content = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                try:
                    data = json.loads(content)
                    return self._format_result(data)
                except:
                    return f"✅ {content[:500]}..." if len(content) > 500 else f"✅ {content}"
            return "✅ Opdracht uitgevoerd (geen output)"
        except Exception as e:
            error_msg = str(e)
            return f"❌ Fout bij uitvoeren tool '{tool_name}': {error_msg}"
    
    def _format_result(self, data: Any) -> str:
        # Deze functie blijft ongewijzigd
        if isinstance(data, dict) and 'items' in data and 'total_count' in data:
            total = data['total_count']
            items = data['items']
            if total == 0: return "📭 Geen resultaten gevonden"
            output = f"📋 {total} resultaten gevonden:\n"
            for i, item in enumerate(items[:5]):
                if isinstance(item, dict):
                    title = item.get('full_name') or item.get('name') or item.get('title') or f"Item {i+1}"
                    desc = item.get('description')
                    output += f"  • {title}"
                    if desc: output += f" - {desc[:60]}\n"
                    else: output += "\n"
                else: output += f"  • {str(item)[:80]}\n"
            if len(items) > 5: output += f"\n... en nog {len(items) - 5} meer."
            return output
        if isinstance(data, list):
            if not data: return "📭 Geen resultaten gevonden"
            output = f"📋 {len(data)} resultaten gevonden:\n"
            for i, item in enumerate(data[:5]):
                if isinstance(item, dict):
                    title = item.get('full_name') or item.get('name') or item.get('title') or f"Item {i+1}"
                    output += f"  • {title}\n"
                else: output += f"  • {str(item)[:80]}\n"
            if len(data) > 5: output += f"\n... en nog {len(data) - 5} meer."
            return output
        if isinstance(data, dict):
            return "📄 Resultaat:\n" + json.dumps(data, indent=2, ensure_ascii=False)
        return f"✅ {str(data)[:200]}"
    
    async def cleanup(self):
        if self.exit_stack:
            await self.exit_stack.aclose()
            self.connected = False
            print("🧹 Verbindingen netjes afgesloten")

# --- BIJGEWERKTE FastAPI SECTIE ---

# Maak een globale 'agent' instantie
agent = AgnoAI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code die bij het opstarten wordt uitgevoerd
    print("🚀 AgnoAI server opstarten...")
    if not agent._configure_llm() or not await agent.connect_github():
        print("💥 Kritieke fout bij opstarten. De server draait, maar zal niet werken.")
    else:
        print("✅ Server is klaar om verzoeken te ontvangen.")
    
    yield  # Hier draait de applicatie terwijl de server aan staat
    
    # Code die bij het afsluiten wordt uitgevoerd
    print("👋 AgnoAI server afsluiten...")
    await agent.cleanup()

# Maak de FastAPI app met de nieuwe lifespan manager
app = FastAPI(title="AgnoAI Server", lifespan=lifespan)


# Sta Cross-Origin verzoeken toe (nodig om de browser met de server te laten praten)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Voor lokaal gebruik is "*" prima
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definieer het request model voor het commando
class CommandRequest(BaseModel):
    command: str

@app.post("/api/command")
async def handle_command(request: CommandRequest):
    """API endpoint om een commando te verwerken."""
    if not agent.connected or not agent.llm_model:
        raise HTTPException(status_code=503, detail="Agent is niet klaar. Check de server logs.")
    
    try:
        result = await agent.process_command(request.command)
        return {"response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interne serverfout: {e}")

@app.get("/")
def read_root():
    return {"message": "Welkom bij de AgnoAI server. Gebruik het /api/command endpoint om commando's te sturen."}

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Start de server met Uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

