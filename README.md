<div align="center">

<h1>🤖 SimpleContext-Bot</h1>

<p><strong>AI Telegram Bot powered by <a href="https://github.com/zacxyonly/SimpleContext">SimpleContext</a></strong><br/>
Setup wizard · Auto-routing agents · Works with Gemini, OpenAI, Ollama</p>

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-2CA5E0?style=flat-square&logo=telegram)](https://telegram.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![SimpleContext](https://img.shields.io/badge/Powered%20by-SimpleContext%20v4.2-blueviolet?style=flat-square)](https://github.com/zacxyonly/SimpleContext)
[![Plugins](https://img.shields.io/badge/Plugins-SimpleContext--Plugin-orange?style=flat-square)](https://github.com/zacxyonly/SimpleContext-Plugin)

</div>

---

## ✨ What is this?

SimpleContext-Bot is a **ready-to-run Telegram bot** that uses [SimpleContext](https://github.com/zacxyonly/SimpleContext) as its AI brain.

A built-in setup wizard **automatically downloads** the engine and agents, then walks you through configuration step by step.

---

## 🚀 Installation

### 1. Clone & Install

```bash
git clone https://github.com/zacxyonly/SimpleContext-Bot.git
cd SimpleContext-Bot
pip install .
```

### 2. Run Setup Wizard

```bash
simplecontext-bot setup
```

The wizard will handle everything:

```
Step 1/6  Download SimpleContext engine from GitHub   ✅
Step 2/6  Download 9 agent definitions                ✅
Step 3/6  Plugin Ecosystem (Optional)                 → pilih plugin yang diinginkan
Step 4/6  Telegram Bot Token                          → paste from @BotFather
Step 5/6  LLM Provider & API Key                      → choose Gemini/OpenAI/Ollama
Step 6/6  Final configuration                         ✅ Done!
```

### 3. Start

```bash
simplecontext-bot start
```

---

## 🔑 Getting Your Tokens

**Telegram Bot Token**
1. Open Telegram → search `@BotFather`
2. Send `/newbot` and follow the steps
3. Copy the token

**Gemini API Key** *(free, recommended)*
1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Click **Create API Key** → copy

**OpenAI API Key**
1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click **Create new secret key** → copy

**Ollama** *(local, no API key needed)*
1. Install from [ollama.ai](https://ollama.ai)
2. Run `ollama pull llama3`
3. Make sure Ollama is running before starting the bot

---

## 🧠 Powered By

| | Repo | Role |
|---|---|---|
| **SimpleContext** | [→](https://github.com/zacxyonly/SimpleContext) | AI brain — tiered memory, context scoring, intent planning |
| **SimpleContext-Agents** | [→](https://github.com/zacxyonly/SimpleContext-Agents) | 9 ready-to-use agent definitions |
| **SimpleContext-Plugin** | [→](https://github.com/zacxyonly/SimpleContext-Plugin) | Official plugin registry — extend bot capabilities |
| **LiteLLM** | pip | Universal LLM connector |

---

## 🎯 Auto-Routing

No need to manually switch agents. The bot detects the best agent for every message automatically:

```
"ada bug di python saya"   →  🖥️  coding
"deploy ke server nginx"   →  🚀  devops
"tulis caption instagram"  →  ✍️  writer
"terjemahkan ke english"   →  🌐  translator
"jelaskan konsep ini"      →  📚  tutor
"ringkas artikel ini"      →  📝  summarizer
"cek fakta berita ini"     →  🔍  researcher
"komplain order saya"      →  🎧  customer_service
"analisis data penjualan"  →  📊  analyst
```

---

## 🤖 Available Agents

| | Agent | Description |
|---|---|---|
| 🖥️ | `coding` | Expert programmer — debug, review, all languages |
| 🚀 | `devops` | Server, Docker, CI/CD, Linux infrastructure |
| ✍️ | `writer` | Content, copywriting, email, social media |
| 📊 | `analyst` | Data analysis, business insights, KPIs |
| 🎧 | `customer_service` | Empathetic CS, complaint handling |
| 🌐 | `translator` | Multi-language, idiom-aware translation |
| 📚 | `tutor` | Patient adaptive teacher for any subject |
| 🔍 | `researcher` | Fact-checking, research, source evaluation |
| 📝 | `summarizer` | Condense any content into clear summaries |

---

## 💬 Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome message, saves your name |
| `/help` | Show all commands |
| `/agents` | List available agents |
| `/agent <name>` | Switch to a specific agent |
| `/agent auto` | Back to auto-routing |
| `/clear` | Clear conversation history |
| `/status` | Show current agent and stats |
| `/memory` | Show your saved profile |
| `/plugins` | List installed plugins & available plugins |
| `/semantic <query>` | Search memory by meaning (requires vector-search plugin) |

---


## 🔌 Plugin Ecosystem

SimpleContext-Bot dapat diperluas dengan plugin dari [SimpleContext-Plugin](https://github.com/zacxyonly/SimpleContext-Plugin).

### Plugin yang tersedia

| Plugin | Deskripsi | Tested ✅ |
|--------|-----------|-----------|
| [`vector-search`](https://github.com/zacxyonly/SimpleContext-Plugin/tree/main/official/plugin-vector-search) | Semantic similarity search — temukan memory berdasarkan makna, bukan kata persis | ✅ |

### Install plugin

**Saat setup wizard** — wizard akan menawarkan plugin secara otomatis di Step 3.

**Setelah setup:**
```bash
# List semua plugin
simplecontext-bot plugins list

# Install plugin
simplecontext-bot plugins install vector-search

# Hapus plugin
simplecontext-bot plugins remove vector-search
```

### Demo plugin via bot

```
/plugins
→ ✅ Vector Search — Semantic similarity search
→ Install lebih banyak di: SimpleContext-Plugin

/semantic kenangan liburan
→ 1. [Semantic | █████ 84%] user suka pantai dan hiking ...
→ 2. [Episodic | ███░░ 67%] sesi kemarin bahas rencana trip ...
```

---

## ⚙️ CLI Commands

```bash
simplecontext-bot setup                # First-time setup wizard (includes plugin selection)
simplecontext-bot start                # Start the bot
simplecontext-bot start --debug        # Start with verbose logging
simplecontext-bot status               # Show configuration
simplecontext-bot status --test        # Check + test LLM connection
simplecontext-bot agents               # List installed agents
simplecontext-bot update               # Update engine + agents
simplecontext-bot update --engine-only # Update engine only
simplecontext-bot update --agents-only # Update agents only
simplecontext-bot plugins list         # List all plugins
simplecontext-bot plugins install <id> # Install a plugin
simplecontext-bot plugins remove <id>  # Remove a plugin
```

---

## 📁 Files After Setup

Everything is stored in `~/.simplecontext-bot/`:

```
~/.simplecontext-bot/
├── config.json        ← your settings (tokens, LLM config)
├── bot.db             ← conversation memory (SQLite)
├── simplecontext/     ← SimpleContext engine (auto-downloaded)
├── agents/            ← agent YAML files (auto-downloaded)
│   ├── coding.yaml
│   ├── devops.yaml
│   └── ...
└── plugins/           ← installed plugins (auto-downloaded via wizard)
    └── vector_search_plugin.py
```

---

## 🔧 Troubleshooting

**Something not working?**
```bash
simplecontext-bot status --test
```

**Update engine and agents:**
```bash
simplecontext-bot update
```

**Start fresh:**
```bash
rm -rf ~/.simplecontext-bot
simplecontext-bot setup
```

---

## 🔗 Ecosystem

| Repositori | Deskripsi |
|------------|----------|
| [SimpleContext](https://github.com/zacxyonly/SimpleContext) | Core engine — Universal AI Brain |
| [SimpleContext-Plugin](https://github.com/zacxyonly/SimpleContext-Plugin) | Plugin registry — extend with semantic search, summarizer, and more |
| [SimpleContext-Bot](https://github.com/zacxyonly/SimpleContext-Bot) | This repo — Telegram Bot |
| [SimpleContext-Agents](https://github.com/zacxyonly/SimpleContext-Agents) | Ready-to-use agent definitions |

---

<div align="center">

Built with ❤️ on top of [SimpleContext](https://github.com/zacxyonly/SimpleContext)

**[⭐ Star the engine repo](https://github.com/zacxyonly/SimpleContext)** if you find this useful!

</div>
