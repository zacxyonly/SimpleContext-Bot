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
    parser.add_argument("--version", action="version", version="%(prog)s 1.2.0")
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

    # plugins
    p_plugins = subparsers.add_parser("plugins", help="Manage plugins")
    p_plugins.set_defaults(func=cmd_plugins)
    plugin_sub = p_plugins.add_subparsers(dest="plugin_action")

    p_plist = plugin_sub.add_parser("list", help="List plugins")
    p_plist.set_defaults(plugin_action="list")

    p_pinstall = plugin_sub.add_parser("install", help="Install a plugin")
    p_pinstall.add_argument("plugin_id", nargs="?", help="Plugin ID (e.g. vector-search)")
    p_pinstall.set_defaults(plugin_action="install")

    p_premove = plugin_sub.add_parser("remove", help="Remove a plugin")
    p_premove.add_argument("plugin_id", nargs="?", help="Plugin ID to remove")
    p_premove.set_defaults(plugin_action="remove")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Default plugin subcommand ke list
    if args.command == "plugins" and not getattr(args, "plugin_action", None):
        args.plugin_action = "list"

    args.func(args)


if __name__ == "__main__":
    main()


def cmd_plugins(args):
    """Manage plugins."""
    from . import config as cfg
    from .installer import (
        OFFICIAL_PLUGINS, get_installed_plugins,
        install_selected_plugins, get_plugin_config,
        check_plugin,
    )
    from .config import DEFAULT_DIR

    install_dir = Path(cfg.get("install_dir", str(DEFAULT_DIR)))

    if args.plugin_action == "list":
        installed = get_installed_plugins(install_dir)
        print(f"\n🔌 Plugins\n" + "─" * 40)
        for pid, info in OFFICIAL_PLUGINS.items():
            status = "✅ installed" if pid in installed else "➕ available"
            print(f"  {status}  {info['label']:<20} {info['description']}")
        if not installed:
            print("\n  Install dengan:")
            for pid in OFFICIAL_PLUGINS:
                print(f"  simplecontext-bot plugins install {pid}")
        print()

    elif args.plugin_action == "install":
        plugin_id = args.plugin_id
        if not plugin_id:
            print("❌ Tentukan nama plugin. Contoh: simplecontext-bot plugins install vector-search")
            return
        if plugin_id not in OFFICIAL_PLUGINS:
            print(f"❌ Plugin '{plugin_id}' tidak dikenal.")
            print(f"   Tersedia: {', '.join(OFFICIAL_PLUGINS.keys())}")
            return
        if check_plugin(install_dir, plugin_id):
            print(f"✅ Plugin '{plugin_id}' sudah terinstall.")
            return

        print(f"\n📥 Installing {OFFICIAL_PLUGINS[plugin_id]['label']}...")
        results = install_selected_plugins(install_dir, [plugin_id])
        if results.get(plugin_id):
            # Update config
            installed = cfg.get("plugins.installed", [])
            if plugin_id not in installed:
                installed.append(plugin_id)
            cfg.set_value("plugins.installed", installed)
            cfg.set_value("plugins.enabled", True)
            plugin_cfgs = cfg.get("plugins.configs", {})
            plugin_cfgs[plugin_id] = get_plugin_config(plugin_id)
            cfg.set_value("plugins.configs", plugin_cfgs)
            print(f"\n✅ Plugin '{plugin_id}' berhasil diinstall!")
            print("   Restart bot untuk mengaktifkan: simplecontext-bot start")
        else:
            print(f"\n❌ Gagal install plugin '{plugin_id}'.")

    elif args.plugin_action == "remove":
        plugin_id = args.plugin_id
        if not check_plugin(install_dir, plugin_id):
            print(f"❌ Plugin '{plugin_id}' tidak terinstall.")
            return
        info     = OFFICIAL_PLUGINS.get(plugin_id, {})
        filepath = install_dir / "plugins" / info.get("file", "")
        if filepath.exists():
            filepath.unlink()
        installed = cfg.get("plugins.installed", [])
        if plugin_id in installed:
            installed.remove(plugin_id)
        cfg.set_value("plugins.installed", installed)
        print(f"✅ Plugin '{plugin_id}' dihapus. Restart bot untuk menerapkan perubahan.")
