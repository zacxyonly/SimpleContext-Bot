<div align="center">

<h1>🤖 SimpleContext-Bot</h1>

<p><strong>AI Telegram Bot powered by <a href="https://github.com/zacxyonly/SimpleContext">SimpleContext</a></strong><br/>
Setup wizard · 15 agents · Dynamic plugins · Works with Gemini, OpenAI, Ollama</p>

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-2CA5E0?style=flat-square&logo=telegram)](https://telegram.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![SimpleContext](https://img.shields.io/badge/Powered%20by-SimpleContext%20v4.3-blueviolet?style=flat-square)](https://github.com/zacxyonly/SimpleContext)
[![Plugins](https://img.shields.io/badge/Plugins-Dynamic%20Auto--Load-brightgreen?style=flat-square)](https://github.com/zacxyonly/SimpleContext-Plugin)
[![PyPI](https://img.shields.io/badge/PyPI-simplecontext--bot-orange?style=flat-square)](https://pypi.org/project/simplecontext-bot/)

</div>

---

## ✨ What is this?

SimpleContext-Bot is a **ready-to-run Telegram bot** powered by [SimpleContext](https://github.com/zacxyonly/SimpleContext) — a structured AI brain with tiered memory, intent planning, and context scoring.

A built-in setup wizard **automatically downloads** the engine, 15 agents, and optional plugins — then walks you through configuration step by step.

---

## 🚀 Installation

### Option A — pip (recommended)

```bash
pip install simplecontext-bot
simplecontext-bot setup
simplecontext-bot start
```

### Option B — from source

```bash
git clone https://github.com/zacxyonly/SimpleContext-Bot.git
cd SimpleContext-Bot
pip install .
simplecontext-bot setup
simplecontext-bot start
```

---

## 🧙 Setup Wizard

```bash
simplecontext-bot setup
```

The wizard handles everything in 6 steps:

```
═══════════════════════════════════════════════════════
  🧠 SimpleContext-Bot — Setup Wizard
═══════════════════════════════════════════════════════

Step 1/6  Download SimpleContext engine        ✅
Step 2/6  Download 15 agent definitions        ✅
Step 3/6  Plugin Ecosystem (Optional)
           Install Vector Search? [y/N]: y     ✅
           Install Summarizer?    [y/N]: y     ✅
Step 4/6  Telegram Bot Token                   → paste from @BotFather
Step 5/6  LLM Provider & API Key               → Gemini / OpenAI / Ollama
Step 6/6  Final configuration                  ✅ Done!
```

---

## 🔑 Getting Your Tokens

**Telegram Bot Token**
1. Open Telegram → search `@BotFather`
2. Send `/newbot` → follow the steps → copy the token

**Gemini API Key** *(free, recommended)*
1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Click **Create API Key** → copy

**OpenAI API Key**
1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click **Create new secret key** → copy

**Ollama** *(local, free, no API key)*
1. Install from [ollama.ai](https://ollama.ai)
2. `ollama pull llama3`
3. Make sure Ollama is running before starting the bot

---

## 🎯 Auto-Routing

No need to manually switch agents. The bot detects the best agent automatically:

```
"ada bug di python saya"     →  🖥️  coding
"deploy ke server nginx"     →  🚀  devops
"tulis caption instagram"    →  ✍️  writer
"terjemahkan ke english"     →  🌐  translator
"jelaskan konsep ini"        →  📚  tutor
"ringkas artikel ini"        →  📝  summarizer
"cek fakta berita ini"       →  🔍  researcher
"komplain order saya"        →  🎧  customer_service
"analisis data penjualan"    →  📊  analyst
"bantu investasi saham"      →  💰  finance
"cek kontrak ini"            →  ⚖️  legal
"brainstorm ide startup"     →  🎨  creative
"tips produktivitas"         →  ⚡  productivity
"olahraga untuk pemula"      →  💪  health
```

---

## 🤖 Available Agents (15)

### Core
| | Agent | Description |
|---|---|---|
| 🧠 | `general` | Default fallback — smart routing to specialized agents |
| 🖥️ | `coding` | Expert programmer — debug, review, all languages |
| 🚀 | `devops` | Server, Docker, CI/CD, Linux infrastructure |
| ✍️ | `writer` | Content, copywriting, email, social media |

### Knowledge & Research
| | Agent | Description |
|---|---|---|
| 🔍 | `researcher` | Fact-checking, research, source evaluation |
| 📚 | `tutor` | Patient adaptive teacher for any subject |
| 📝 | `summarizer` | Condense any content into clear summaries |
| 🌐 | `translator` | Multi-language, idiom-aware translation |

### Business & Professional
| | Agent | Description |
|---|---|---|
| 📊 | `analyst` | Data analysis, business insights, KPIs |
| 🎧 | `customer_service` | Empathetic CS, complaint handling |
| 💰 | `finance` | Budgeting, investing, financial planning |
| ⚖️ | `legal` | Contracts, rights, Indonesian law reference |

### Lifestyle & Creativity
| | Agent | Description |
|---|---|---|
| 🎨 | `creative` | Brainstorming, storytelling, naming, worldbuilding |
| ⚡ | `productivity` | Time management, habits, GTD, focus systems |
| 💪 | `health` | Fitness, nutrition, sleep, mental wellness |

---

## 💬 Bot Commands

### Built-in Commands
| Command | Description |
|---|---|
| `/start` | Welcome message, saves your name |
| `/help` | Show all commands including plugin commands |
| `/agents` | List all available agents |
| `/agent <n>` | Switch to a specific agent |
| `/agent auto` | Back to auto-routing |
| `/clear` | Clear conversation history (keeps profile) |
| `/status` | Show current agent, message count, active plugins |
| `/memory` | Show your saved profile |
| `/plugins` | List active plugins and their commands |

### Plugin Commands (auto-registered)
Plugin commands register automatically when a plugin is loaded:

| Command | Plugin Required | Description |
|---|---|---|
| `/semantic <query>` | `vector-search` | Search memory by meaning |
| `/summary` | `summarizer` | Summarize conversation |
| `/search <query>` | `web-search` | Search the internet |
| `/translate <lang>` | `translate` | Set language or translate |
| `/sentiment` | `sentiment` | View sentiment analysis |
| `/analytics` | `analytics` | View usage statistics |
| `/usage` | `rate-limiter` | Check your usage quota |

---

## 🔌 Plugin Ecosystem

Extend the bot with plugins from [SimpleContext-Plugin](https://github.com/zacxyonly/SimpleContext-Plugin).

### Available Official Plugins

| Plugin | Description |
|--------|-------------|
| `vector-search` | Semantic memory search — find by meaning, not exact words |
| `analytics` | Usage statistics per user and agent |
| `summarizer` | Auto-compress conversation to episodic memory via LLM |
| `web-search` | Real-time internet search (DuckDuckGo free, Bing, Google) |
| `translate` | Multi-language — auto-detect 20+ languages |
| `sentiment` | Sentiment analysis — adapts agent tone when user is frustrated |
| `rate-limiter` | Limit requests per hour/day, token estimation |

### Install Plugins

```bash
simplecontext-bot plugins list                    # fetch list from GitHub registry
simplecontext-bot plugins install vector-search   # install a plugin
simplecontext-bot plugins install summarizer
simplecontext-bot plugins remove vector-search    # remove a plugin
```

**Manual (community plugins):**
```bash
cp my_plugin.py ~/.simplecontext-bot/plugins/
simplecontext-bot start   # auto-detected on startup
```

### How Plugin Commands Work

Plugins declare their own Telegram commands via `app_commands` (SimpleContext v4.3 standard).
The bot registers them automatically — no code changes needed:

```python
class MyPlugin(BasePlugin):
    app_commands = {
        "mycommand": {
            "description": "What this does",
            "usage":       "/mycommand <arg>",
            "handler":     "handle_mycommand",
        }
    }

    async def handle_mycommand(self, ctx: AppCommandContext) -> str:
        return f"Hello from {ctx.platform}! Query: {ctx.args_str}"
```

Drop the file → restart → `/mycommand` is live in Telegram.

---

## ⚙️ CLI Commands

```bash
# Setup & Start
simplecontext-bot setup                   # First-time setup wizard
simplecontext-bot start                   # Start the bot
simplecontext-bot start --debug           # Start with verbose logging

# Status & Info
simplecontext-bot status                  # Show configuration summary
simplecontext-bot status --test           # Check + test LLM connection
simplecontext-bot dashboard               # Show usage stats and system info
simplecontext-bot agents                  # List installed agents

# Update
simplecontext-bot update                  # Update engine + agents + plugins
simplecontext-bot update --engine-only    # Update engine only
simplecontext-bot update --agents-only    # Update agents only
simplecontext-bot update --plugins-only   # Update installed plugins only

# Plugins
simplecontext-bot plugins list            # List plugins (fetches from GitHub)
simplecontext-bot plugins install <id>    # Install a plugin
simplecontext-bot plugins remove <id>     # Remove a plugin

# Config (change any value without re-running setup)
simplecontext-bot set llm.api_key <key>   # Update API key
simplecontext-bot set llm.model <model>   # Change LLM model
simplecontext-bot set llm.provider <p>    # Switch provider (gemini/openai/ollama)
simplecontext-bot set telegram.token <t>  # Update Telegram token
simplecontext-bot set bot.debug true      # Enable debug logging
simplecontext-bot set bot.memory_limit 30 # Increase memory limit
```

---

## 📊 Dashboard

```bash
simplecontext-bot dashboard
```

```
╔══════════════════════════════════════════════════╗
║         SimpleContext-Bot Dashboard              ║
╚══════════════════════════════════════════════════╝

  🔧 System
  ──────────────────────────────────────────────────
  Engine     : ✅ Installed
  DB size    : 2.4 MB
  Telegram   : ✅ Configured

  🤖 Agents & Plugins
  ──────────────────────────────────────────────────
  Agents     : 15 installed
  Plugins    : 2 installed  (vector_search_plugin, summarizer_plugin)

  🧠 LLM
  ──────────────────────────────────────────────────
  Provider   : gemini
  Model      : gemini/gemini-2.0-flash

  📊 Usage Stats
  ──────────────────────────────────────────────────
  Users      : 42
  Nodes      : 1,847
```

---

## 📁 Files After Setup

```
~/.simplecontext-bot/
├── config.json          ← settings (tokens, LLM, plugins)
├── bot.db               ← conversation memory (SQLite)
├── simplecontext/       ← engine (auto-downloaded)
├── agents/              ← 15 agent YAML files (auto-downloaded)
│   ├── general.yaml
│   ├── coding.yaml
│   └── ...
└── plugins/             ← installed plugins
    ├── vector_search_plugin.py
    └── summarizer_plugin.py
```

---

## 🔧 Troubleshooting

**Diagnose issues:**
```bash
simplecontext-bot status --test
```

**Update everything:**
```bash
simplecontext-bot update
```

**Change a config value without re-running setup:**
```bash
simplecontext-bot set llm.api_key <new-key>
simplecontext-bot set llm.model gemini/gemini-2.5-flash
simplecontext-bot set telegram.token <new-token>
```

**Start fresh:**
```bash
rm -rf ~/.simplecontext-bot
simplecontext-bot setup
```

---

## 🧠 Powered By

| Repo | Role |
|------|------|
| [SimpleContext](https://github.com/zacxyonly/SimpleContext) | AI brain — tiered memory, context scoring, intent planning |
| [SimpleContext-Agents](https://github.com/zacxyonly/SimpleContext-Agents) | 15 ready-to-use agent definitions |
| [SimpleContext-Plugin](https://github.com/zacxyonly/SimpleContext-Plugin) | Official plugin registry |
| [LiteLLM](https://github.com/BerriAI/litellm) | Universal LLM connector |

---

## 🔗 Ecosystem

| Repo | Description |
|------|-------------|
| [SimpleContext](https://github.com/zacxyonly/SimpleContext) | Core engine — Universal AI Brain |
| [SimpleContext-Agents](https://github.com/zacxyonly/SimpleContext-Agents) | Ready-to-use agent definitions |
| [SimpleContext-Plugin](https://github.com/zacxyonly/SimpleContext-Plugin) | Plugin registry |
| [SimpleContext-Bot](https://github.com/zacxyonly/SimpleContext-Bot) | This repo |
| [SimpleContext-Docs](https://github.com/zacxyonly/SimpleContext-Docs) | Full documentation |

---

<div align="center">

Built with ❤️ on top of [SimpleContext](https://github.com/zacxyonly/SimpleContext)

**[⭐ Star the engine repo](https://github.com/zacxyonly/SimpleContext)** if you find this useful!

</div>
