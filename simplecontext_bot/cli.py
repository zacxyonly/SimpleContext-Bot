"""
cli.py — Command Line Interface
Commands: setup, start, status, agents, update
"""

import sys
import argparse
import logging
from pathlib import Path


def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=level,
    )


def cmd_setup(args):
    """Run setup wizard."""
    from .setup_wizard import run_wizard
    run_wizard()


def cmd_start(args):
    """Start the Telegram bot."""
    from . import config as cfg

    if not cfg.is_configured():
        print("❌ Bot not configured yet.")
        print("   Run: simplecontext-bot setup")
        sys.exit(1)

    setup_logging(debug=cfg.get("bot.debug", False))

    print("🧠 Starting SimpleContext-Bot...")
    from .bot import run
    run()


def cmd_status(args):
    """Show current status and configuration."""
    from . import config as cfg
    from .installer import check_engine, check_agents, get_installed_agents
    from .config import DEFAULT_DIR

    install_dir = Path(cfg.get("install_dir", str(DEFAULT_DIR)))

    print("\n📊 SimpleContext-Bot Status\n" + "─" * 40)

    # Engine
    engine_ok = check_engine(install_dir)
    print(f"  Engine:      {'✅ Installed' if engine_ok else '❌ Not installed'}")

    # Agents
    agents = get_installed_agents(install_dir)
    print(f"  Agents:      {'✅ ' + str(len(agents)) + ' installed' if agents else '❌ None'}")
    if agents:
        print(f"               {', '.join(agents)}")

    # Telegram
    token = cfg.get("telegram.token", "")
    print(f"  Telegram:    {'✅ Token configured' if token else '❌ Not configured'}")

    # LLM
    provider = cfg.get("llm.provider", "")
    model    = cfg.get("llm.model", "")
    api_key  = cfg.get("llm.api_key", "")
    llm_ok   = bool(provider and model and (api_key or provider == "ollama"))
    print(f"  LLM:         {'✅ ' + provider + ' / ' + model if llm_ok else '❌ Not configured'}")

    # Test LLM
    if llm_ok and args.test:
        print("\n  Testing LLM connection...")
        from .llm import test_connection
        success, msg = test_connection()
        print(f"  {msg}")

    print()
    if not cfg.is_configured():
        print("  Run `simplecontext-bot setup` to configure.\n")


def cmd_agents(args):
    """List available agents."""
    from .installer import get_installed_agents, DEFAULT_DIR
    from . import config as cfg

    install_dir = Path(cfg.get("install_dir", str(DEFAULT_DIR)))
    agents      = get_installed_agents(install_dir)

    if not agents:
        print("❌ No agents installed. Run: simplecontext-bot setup")
        return

    print(f"\n🤖 Installed Agents ({len(agents)})\n" + "─" * 40)

    agents_dir = install_dir / "agents"
    for name in sorted(agents):
        yaml_path = agents_dir / f"{name}.yaml"
        try:
            # Read description from YAML
            with open(yaml_path) as f:
                content = f.read()
            desc = ""
            for line in content.splitlines():
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip()
                    break
            print(f"  • {name:<20} {desc}")
        except Exception:
            print(f"  • {name}")
    print()


def cmd_update(args):
    """Update engine and/or agents."""
    from . import config as cfg
    from .installer import update_engine, update_agents
    from .config import DEFAULT_DIR

    install_dir = Path(cfg.get("install_dir", str(DEFAULT_DIR)))

    if args.engine_only:
        update_engine(install_dir)
    elif args.agents_only:
        update_agents(install_dir)
    else:
        print("🔄 Updating SimpleContext-Bot...\n")
        update_engine(install_dir)
        update_agents(install_dir)
        print("\n✅ Update complete!")


def main():
    """Entry point untuk simplecontext-bot command."""
    parser = argparse.ArgumentParser(
        prog="simplecontext-bot",
        description="🧠 SimpleContext-Bot — AI Telegram Bot powered by SimpleContext",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # setup
    p_setup = subparsers.add_parser("setup", help="Run setup wizard")
    p_setup.set_defaults(func=cmd_setup)

    # start
    p_start = subparsers.add_parser("start", help="Start the bot")
    p_start.add_argument("--debug", action="store_true", help="Enable debug logging")
    p_start.set_defaults(func=cmd_start)

    # status
    p_status = subparsers.add_parser("status", help="Show bot status")
    p_status.add_argument("--test", action="store_true", help="Test LLM connection")
    p_status.set_defaults(func=cmd_status)

    # agents
    p_agents = subparsers.add_parser("agents", help="List installed agents")
    p_agents.set_defaults(func=cmd_agents)

    # update
    p_update = subparsers.add_parser("update", help="Update engine and agents")
    p_update.add_argument("--engine-only", action="store_true")
    p_update.add_argument("--agents-only", action="store_true")
    p_update.set_defaults(func=cmd_update)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
