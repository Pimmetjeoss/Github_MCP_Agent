# 🤖 AgnoAI - GitHub MCP Agent

AgnoAI is een intelligente AI-assistent die via een webinterface natuurlijke taal commando's omzet naar GitHub acties. Het project combineert Google's Gemini AI met het Model Context Protocol (MCP) om een naadloze ervaring te bieden voor GitHub management.

## ✨ Features

- **🧠 Intelligente AI-verwerking**: Gebruikt Google Gemini 1.5 Flash voor natuurlijke taalverwerking
- **🔗 GitHub integratie**: Volledige GitHub API toegang via MCP (Model Context Protocol)
- **🌐 Webinterface**: Moderne chat-interface voor eenvoudige interactie
- **📡 FastAPI backend**: Snelle en betrouwbare REST API
- **🔄 Real-time communicatie**: Direct feedback en resultaten

## 🛠️ Technische Stack

- **Backend**: Python 3.8+ met FastAPI
- **AI Model**: Google Gemini 1.5 Flash
- **GitHub Integration**: MCP GitHub Server
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Server**: Uvicorn ASGI server

## 📋 Vereisten

- **Python 3.8+**
- **Node.js en npm** (voor MCP GitHub server)
- **Google Gemini API Key**
- **GitHub Personal Access Token**

## 🚀 Installatie

### 1. Clone de repository
```bash
git clone https://github.com/Pimmetjeoss/Github_MCP_Agent.git
cd Github_MCP_Agent
```

### 2. Installeer Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Configureer environment variabelen
Maak een `.env` bestand in de root directory:
```env
GEMINI_API_KEY=jouw_gemini_api_key_hier
GITHUB_TOKEN=jouw_github_personal_access_token_hier
```

#### Hoe verkrijg je de API keys?

**Google Gemini API Key:**
1. Ga naar [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Maak een nieuwe API key aan
3. Kopieer de key naar je `.env` bestand

**GitHub Personal Access Token:**
1. Ga naar GitHub → Settings → Developer settings → Personal access tokens
2. Genereer een nieuwe token met de benodigde rechten (repo, read:user, etc.)
3. Kopieer de token naar je `.env` bestand

### 4. Start de server
```bash
python agno_ai_improved.py
```

De server draait nu op `http://127.0.0.1:8000`

### 5. Open de webinterface
Open `index.html` in je browser of ga naar `http://127.0.0.1:8000` (als je een statische file server hebt geconfigureerd).

## 💬 Gebruik

### Voorbeelden van commando's:

- **"lijst mijn repositories"** - Toont al je GitHub repositories
- **"zoek naar machine learning projecten in Python"** - Zoekt publieke repositories
- **"maak een issue aan in mijn-repo met titel 'Bug' en tekst 'Er is een probleem'"** - Maakt een nieuwe issue
- **"fork het repository owner/project"** - Forkt een repository naar jouw account

### Ondersteunde GitHub acties:

- 📂 Repository management (zoeken, maken, forken)
- 🐛 Issue management (maken, bijwerken, commentaar)
- 🔄 Pull request operations  
- 👥 Collaborator management
- 📁 File operations (lezen, schrijven, uploaden)
- 🌳 Branch management

## 🏗️ Architectuur

```
┌─────────────────┐    HTTP    ┌─────────────────┐    MCP     ┌─────────────────┐
│   Frontend      │ ────────► │   FastAPI       │ ─────────► │   GitHub MCP    │
│   (index.html)  │           │   Server        │            │   Server        │
└─────────────────┘           └─────────────────┘            └─────────────────┘
                                       │                              │
                                       ▼                              │
                              ┌─────────────────┐                     │
                              │   Gemini AI     │                     │
                              │   (LLM Brain)   │                     │
                              └─────────────────┘                     │
                                       │                              │
                                       ▼                              ▼
                              ┌─────────────────────────────────────────┐
                              │          GitHub API                     │
                              └─────────────────────────────────────────┘
```

## 📁 Project Structuur

```
Github_MCP_Agent/
├── agno_ai_improved.py    # Main Python server met AI logic
├── index.html             # Frontend webinterface  
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore regels
├── .env                  # Environment variabelen (niet in git)
└── README.md             # Deze documentatie
```

## 🔧 Development

### Code structuur

**AgnoAI Class**: De hoofdklasse die alle functionaliteit beheert
- `_configure_llm()`: Configureert Google Gemini AI
- `connect_github()`: Stelt MCP verbinding met GitHub op
- `process_command()`: Verwerkt natuurlijke taal naar GitHub acties
- `_call_tool_safe()`: Veilige tool execution
- `_format_result()`: Formatteert API responses voor gebruikers

**FastAPI Endpoints**:
- `POST /api/command`: Hoofdendpoint voor commando verwerking
- `GET /`: Basis health check endpoint

### Uitbreidingen

Het project is modulair opgezet en kan eenvoudig worden uitgebreid met:
- Meer AI models (OpenAI, Claude, etc.)
- Andere MCP servers (GitLab, Bitbucket, etc.)
- Geavanceerdere UI componenten
- Database logging
- Gebruikersauthenticatie

## 🐛 Troubleshooting

### Veelvoorkomende problemen:

**"NPX niet gevonden"**
- Installeer Node.js en npm: https://nodejs.org/

**"Geen GEMINI_API_KEY gevonden"**  
- Controleer je `.env` bestand
- Zorg dat de API key geldig is

**"GitHub verbinding mislukt"**
- Controleer je GitHub token rechten
- Test de token handmatig in de GitHub API

**"CORS errors in browser"**
- Zorg dat de FastAPI server draait
- Controleer of de URL in de frontend correct is

## 📜 Licentie

Dit project is open source. Voel je vrij om het te gebruiken en aan te passen volgens jouw behoeften.

## 🤝 Contributeren

Bijdragen zijn welkom! Open een issue of submit een pull request.

## 🆘 Support

Voor vragen of problemen, open een issue in deze repository.

---

**Gemaakt met ❤️ door Pimmetjeoss**