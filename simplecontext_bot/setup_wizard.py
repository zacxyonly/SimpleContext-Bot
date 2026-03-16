"""
setup_wizard.py — Interactive setup wizard
Panduan langkah demi langkah untuk konfigurasi pertama kali.
"""

import sys
from pathlib import Path
from . import config as cfg
from .installer import (
    install_engine, install_agents,
    check_engine, check_agents,
)
from .config import DEFAULT_DIR

# LLM provider configs
LLM_PROVIDERS = {
    "1": {
        "name": "Gemini (Google)",
        "provider": "gemini",
        "models": ["gemini/gemini-2.0-flash", "gemini/gemini-1.5-flash", "gemini/gemini-1.5-pro"],
        "default_model": "gemini/gemini-2.0-flash",
        "key_url": "https://aistudio.google.com/app/apikey",
        "key_label": "Gemini API Key",
        "free_tier": True,
    },
    "2": {
        "name": "OpenAI",
        "provider": "openai",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "default_model": "gpt-4o-mini",
        "key_url": "https://platform.openai.com/api-keys",
        "key_label": "OpenAI API Key",
        "free_tier": False,
    },
    "3": {
        "name": "Ollama (Local, Free)",
        "provider": "ollama",
        "models": ["llama3", "mistral", "phi3", "gemma"],
        "default_model": "llama3",
        "key_url": "https://ollama.ai",
        "key_label": None,  # tidak butuh key
        "free_tier": True,
    },
}


def _print_header():
    print("\n" + "═" * 55)
    print("  🧠 SimpleContext-Bot — Setup Wizard")
    print("═" * 55)
    print("  This wizard will help you configure your bot.")
    print("  Press Ctrl+C at any time to cancel.\n")


def _step(n: int, total: int, title: str):
    print(f"\n{'─' * 55}")
    print(f"  Step {n}/{total}: {title}")
    print("─" * 55)


def _ask(prompt: str, default: str = "", secret: bool = False) -> str:
    """Ask user for input with optional default."""
    if default:
        display = f"{prompt} [{default}]: "
    else:
        display = f"{prompt}: "

    while True:
        try:
            if secret:
                import getpass
                value = getpass.getpass(display).strip()
            else:
                value = input(display).strip()

            if not value and default:
                return default
            if value:
                return value
            print("  ⚠️  This field is required.")
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Setup cancelled.")
            sys.exit(0)


def _ask_choice(prompt: str, choices: dict, default: str = "1") -> str:
    """Ask user to pick from numbered choices."""
    print(f"\n  {prompt}")
    for key, val in choices.items():
        name = val if isinstance(val, str) else val.get("name", val)
        marker = " (default)" if key == default else ""
        print(f"  {key}. {name}{marker}")

    while True:
        choice = input(f"\n  Enter choice [{default}]: ").strip() or default
        if choice in choices:
            return choice
        print(f"  ⚠️  Invalid choice. Pick from: {', '.join(choices.keys())}")


def run_wizard():
    """Run the full setup wizard."""
    _print_header()

    install_dir = Path(cfg.get("install_dir", str(cfg.DEFAULT_DIR)))
    total_steps = 5

    # ── Step 1: Install Engine ────────────────────────────
    _step(1, total_steps, "Download SimpleContext Engine")

    if check_engine(install_dir):
        print("  ✅ SimpleContext engine already installed.")
        reinstall = input("  Reinstall? [y/N]: ").strip().lower()
        if reinstall == "y":
            if not install_engine(install_dir):
                print("  ❌ Failed to install engine. Check your internet connection.")
                sys.exit(1)
    else:
        print("  📥 Downloading SimpleContext engine from GitHub...")
        if not install_engine(install_dir):
            print("  ❌ Failed to install engine. Check your internet connection.")
            sys.exit(1)

    cfg.set_value("simplecontext.engine_dir", str(install_dir / "simplecontext"))

    # ── Step 2: Install Agents ────────────────────────────
    _step(2, total_steps, "Download Agent Definitions")

    if check_agents(install_dir):
        print("  ✅ Agents already installed.")
        reinstall = input("  Reinstall? [y/N]: ").strip().lower()
        if reinstall == "y":
            if not install_agents(install_dir):
                print("  ⚠️  Failed to install agents. Continuing with existing agents.")
    else:
        print("  📥 Downloading agents from SimpleContext-Agents...")
        if not install_agents(install_dir):
            print("  ⚠️  Failed to install agents. You can add agents manually later.")

    cfg.set_value("simplecontext.agents_dir", str(install_dir / "agents"))

    # ── Step 3: Telegram Token ────────────────────────────
    _step(3, total_steps, "Telegram Bot Token")
    print("  Get your token from @BotFather on Telegram:")
    print("  1. Open Telegram → search @BotFather")
    print("  2. Send /newbot")
    print("  3. Follow instructions and copy the token\n")

    token = _ask("  Telegram Bot Token", secret=True)
    cfg.set_value("telegram.token", token)
    print("  ✅ Token saved.")

    # ── Step 4: LLM Provider ──────────────────────────────
    _step(4, total_steps, "LLM Provider")
    print("  Choose your AI model provider:\n")

    provider_choices = {k: v["name"] + (" ⭐ FREE" if v["free_tier"] else "") for k, v in LLM_PROVIDERS.items()}
    choice = _ask_choice("Select provider:", provider_choices, default="1")
    provider_info = LLM_PROVIDERS[choice]

    cfg.set_value("llm.provider", provider_info["provider"])

    # Model selection
    print(f"\n  Available {provider_info['name']} models:")
    model_choices = {str(i+1): m for i, m in enumerate(provider_info["models"])}
    model_choice = _ask_choice("Select model:", model_choices, default="1")
    selected_model = provider_info["models"][int(model_choice) - 1]
    cfg.set_value("llm.model", selected_model)

    # API Key
    if provider_info["key_label"]:
        print(f"\n  Get your API key from: {provider_info['key_url']}")
        api_key = _ask(f"  {provider_info['key_label']}", secret=True)
        cfg.set_value("llm.api_key", api_key)
    else:
        # Ollama — tanya base URL
        print(f"\n  Make sure Ollama is running: https://ollama.ai")
        base_url = _ask("  Ollama URL", default="http://localhost:11434")
        cfg.set_value("llm.base_url", base_url)
        cfg.set_value("llm.api_key", "ollama")

    print(f"  ✅ LLM configured: {provider_info['name']} / {selected_model}")

    # ── Step 5: Final Config ──────────────────────────────
    _step(5, total_steps, "Final Configuration")

    # Default agent
    from .installer import get_installed_agents
    agents = get_installed_agents(install_dir)
    if agents:
        print(f"\n  Available agents: {', '.join(agents)}")
        default_agent = _ask("  Default agent", default="general")
        cfg.set_value("simplecontext.default_agent", default_agent)

    # DB path
    db_path = install_dir / "bot.db"
    cfg.set_value("simplecontext.db_path", str(db_path))

    # Summary
    print("\n" + "═" * 55)
    print("  ✅ Setup Complete!")
    print("═" * 55)
    print(f"\n  📁 Install dir:  {install_dir}")
    print(f"  🤖 LLM:          {provider_info['name']} / {selected_model}")
    print(f"  🧠 Agents:       {len(agents)} installed")
    print(f"\n  To start your bot:")
    print("  \033[1msimplecontext-bot start\033[0m")
    print()
