"""
cli.py — Command Line Interface v1.3
Commands: setup, start, status, agents, update, plugins, dashboard
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


# ── Helpers UI ────────────────────────────────────────────

def _divider(char="─", width=50):
    print(char * width)

def _header(title: str, emoji: str = ""):
    print(f"\n{emoji}  {title}" if emoji else f"\n{title}")
    _divider()

def _ask(prompt: str, default: str = "") -> str:
    display = f"  {prompt} [{default}]: " if default else f"  {prompt}: "
    try:
        val = input(display).strip()
        return val if val else default
    except (KeyboardInterrupt, EOFError):
        print("\n\n  Cancelled.")
        sys.exit(0)

def _confirm(prompt: str, default: bool = False) -> bool:
    hint    = "Y/n" if default else "y/N"
    display = f"  {prompt} [{hint}]: "
    try:
        val = input(display).strip().lower()
        if not val:
            return default
        return val in ("y", "yes", "ya")
    except (KeyboardInterrupt, EOFError):
        return False


# ── Commands ──────────────────────────────────────────────

def cmd_setup(args):
    from .setup_wizard import run_wizard
    run_wizard()


def cmd_start(args):
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
    from . import config as cfg
    from .installer import check_engine, check_agents, get_installed_agents, get_installed_plugins, OFFICIAL_PLUGINS
    from .config import DEFAULT_DIR

    install_dir = Path(cfg.get("install_dir", str(DEFAULT_DIR)))

    _header("SimpleContext-Bot Status", "📊")

    engine_ok = check_engine(install_dir)
    print(f"  Engine:      {'✅ Installed' if engine_ok else '❌ Not installed'}")

    agents = get_installed_agents(install_dir)
    print(f"  Agents:      {'✅ ' + str(len(agents)) + ' installed' if agents else '❌ None'}")
    if agents:
        print(f"               {', '.join(agents)}")

    token  = cfg.get("telegram.token", "")
    print(f"  Telegram:    {'✅ Token configured' if token else '❌ Not configured'}")

    provider = cfg.get("llm.provider", "")
    model    = cfg.get("llm.model", "")
    api_key  = cfg.get("llm.api_key", "")
    llm_ok   = bool(provider and model and (api_key or provider == "ollama"))
    print(f"  LLM:         {'✅ ' + provider + ' / ' + model if llm_ok else '❌ Not configured'}")

    installed_plugins = get_installed_plugins(install_dir)
    if installed_plugins:
        labels = ", ".join(OFFICIAL_PLUGINS[p]["label"] for p in installed_plugins if p in OFFICIAL_PLUGINS)
        print(f"  Plugins:     ✅ {len(installed_plugins)} installed ({labels})")
    else:
        print(f"  Plugins:     — None")

    if llm_ok and args.test:
        print("\n  Testing LLM connection...")
        from .llm import test_connection
        _, msg = test_connection()
        print(f"  {msg}")

    print()
    if not cfg.is_configured():
        print("  Run `simplecontext-bot setup` to configure.\n")


def cmd_agents(args):
    from .installer import get_installed_agents
    from . import config as cfg
    from .config import DEFAULT_DIR

    install_dir = Path(cfg.get("install_dir", str(DEFAULT_DIR)))
    agents      = get_installed_agents(install_dir)

    if not agents:
        print("❌ No agents installed. Run: simplecontext-bot setup")
        return

    _header(f"Installed Agents ({len(agents)})", "🤖")

    agents_dir = install_dir / "agents"
    for name in sorted(agents):
        yaml_path = agents_dir / f"{name}.yaml"
        try:
            with open(yaml_path) as f:
                content = f.read()
            desc = ""
            for line in content.splitlines():
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip()
                    break
            print(f"  • {name:<22} {desc}")
        except Exception:
            print(f"  • {name}")
    print()


def cmd_update(args):
    from . import config as cfg
    from .installer import update_engine, update_agents, update_plugins
    from .config import DEFAULT_DIR

    install_dir = Path(cfg.get("install_dir", str(DEFAULT_DIR)))

    if args.engine_only:
        update_engine(install_dir)
    elif args.agents_only:
        update_agents(install_dir)
    elif getattr(args, "plugins_only", False):
        print("🔄 Updating plugins...\n")
        update_plugins(install_dir)
        print("\n✅ Plugins updated!")
    else:
        print("🔄 Updating SimpleContext-Bot...\n")
        update_engine(install_dir)
        update_agents(install_dir)
        update_plugins(install_dir)
        print("\n✅ Update complete!")


def cmd_plugins(args):
    """Plugin management dengan interactive menu untuk install."""
    from . import config as cfg
    from .installer import (
        OFFICIAL_PLUGINS, get_installed_plugins,
        install_selected_plugins, get_plugin_config,
        check_plugin,
    )
    from .config import DEFAULT_DIR

    install_dir = Path(cfg.get("install_dir", str(DEFAULT_DIR)))
    action      = getattr(args, "plugin_action", "list") or "list"

    if action == "list":
        _plugin_list(install_dir, OFFICIAL_PLUGINS, get_installed_plugins)

    elif action == "install":
        plugin_id = getattr(args, "plugin_id", None)
        if plugin_id:
            # Install langsung jika plugin_id diberikan via argumen
            _plugin_install_direct(
                install_dir, plugin_id, cfg,
                OFFICIAL_PLUGINS, install_selected_plugins,
                get_plugin_config, check_plugin,
            )
        else:
            # Tidak ada argumen → tampilkan interactive menu
            _plugin_install_interactive(
                install_dir, cfg,
                OFFICIAL_PLUGINS, get_installed_plugins,
                install_selected_plugins, get_plugin_config,
            )

    elif action == "remove":
        plugin_id = getattr(args, "plugin_id", None)
        if not plugin_id:
            # Interactive remove menu
            _plugin_remove_interactive(
                install_dir, cfg,
                OFFICIAL_PLUGINS, get_installed_plugins,
            )
        else:
            _plugin_remove_direct(install_dir, plugin_id, cfg, OFFICIAL_PLUGINS, check_plugin)


def _plugin_list(install_dir, OFFICIAL_PLUGINS, get_installed_plugins):
    installed = get_installed_plugins(install_dir)
    _header(f"Plugin Registry ({len(OFFICIAL_PLUGINS)} available)", "🔌")
    for pid, info in OFFICIAL_PLUGINS.items():
        status = "✅ installed" if pid in installed else "  available"
        print(f"  {status}  {info['label']:<22} {info['description']}")
    print()
    if installed:
        print(f"  {len(installed)}/{len(OFFICIAL_PLUGINS)} plugins installed.")
    else:
        print("  No plugins installed.")
        print("  Run: simplecontext-bot plugins install")
    print()


def _plugin_install_interactive(install_dir, cfg, OFFICIAL_PLUGINS,
                                  get_installed_plugins, install_selected_plugins,
                                  get_plugin_config):
    """Menu interaktif untuk memilih dan install plugin."""
    installed = get_installed_plugins(install_dir)
    available = {pid: info for pid, info in OFFICIAL_PLUGINS.items()
                 if pid not in installed}

    _header("Install Plugins", "📥")

    if not available:
        print("  ✅ Semua plugin sudah terinstall!\n")
        return

    # Tampilkan daftar dengan nomor
    pid_list = list(available.keys())
    print("  Pilih plugin yang ingin diinstall.")
    print("  (tekan Enter tanpa input untuk selesai)\n")

    for i, pid in enumerate(pid_list, 1):
        info = available[pid]
        print(f"  {i}. {info['label']}")
        print(f"     {info['description']}\n")

    # Pilihan input
    print("  Masukkan nomor (contoh: 1 3 5) atau 'all' untuk semua:")
    try:
        raw = input("  > ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n  Cancelled.")
        return

    if not raw:
        print("  Tidak ada plugin yang dipilih.")
        return

    # Parse pilihan
    to_install = []
    if raw == "all":
        to_install = pid_list
    else:
        for token in raw.split():
            try:
                idx = int(token) - 1
                if 0 <= idx < len(pid_list):
                    to_install.append(pid_list[idx])
                else:
                    print(f"  ⚠️  Nomor {token} tidak valid, dilewati.")
            except ValueError:
                # Mungkin langsung nama plugin
                if token in available:
                    to_install.append(token)
                else:
                    print(f"  ⚠️  '{token}' tidak dikenal, dilewati.")

    if not to_install:
        print("  Tidak ada plugin valid yang dipilih.")
        return

    # Konfirmasi
    print(f"\n  Plugin yang akan diinstall:")
    for pid in to_install:
        print(f"    • {OFFICIAL_PLUGINS[pid]['label']}")

    if not _confirm("\n  Lanjutkan?", default=True):
        print("  Dibatalkan.")
        return

    # Install
    print()
    results = install_selected_plugins(install_dir, to_install)
    success = []
    failed  = []

    for pid, ok in results.items():
        if ok:
            success.append(pid)
            installed_list = cfg.get("plugins.installed", [])
            if pid not in installed_list:
                installed_list.append(pid)
            cfg.set_value("plugins.installed", installed_list)
            cfg.set_value("plugins.enabled", True)
            plugin_cfgs       = cfg.get("plugins.configs", {})
            plugin_cfgs[pid]  = get_plugin_config(pid)
            cfg.set_value("plugins.configs", plugin_cfgs)
        else:
            failed.append(pid)

    print()
    if success:
        labels = ", ".join(OFFICIAL_PLUGINS[p]["label"] for p in success)
        print(f"  ✅ Berhasil: {labels}")
    if failed:
        labels = ", ".join(OFFICIAL_PLUGINS[p]["label"] for p in failed)
        print(f"  ❌ Gagal: {labels}")

    if success:
        print("\n  Restart bot untuk mengaktifkan:")
        print("  simplecontext-bot start\n")


def _plugin_install_direct(install_dir, plugin_id, cfg, OFFICIAL_PLUGINS,
                             install_selected_plugins, get_plugin_config, check_plugin):
    """Install plugin langsung dari argumen CLI."""
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
        installed = cfg.get("plugins.installed", [])
        if plugin_id not in installed:
            installed.append(plugin_id)
        cfg.set_value("plugins.installed", installed)
        cfg.set_value("plugins.enabled", True)
        plugin_cfgs          = cfg.get("plugins.configs", {})
        plugin_cfgs[plugin_id] = get_plugin_config(plugin_id)
        cfg.set_value("plugins.configs", plugin_cfgs)
        print(f"\n✅ Plugin '{plugin_id}' berhasil diinstall!")
        print("   Restart bot: simplecontext-bot start")
    else:
        print(f"\n❌ Gagal install plugin '{plugin_id}'.")


def _plugin_remove_interactive(install_dir, cfg, OFFICIAL_PLUGINS, get_installed_plugins):
    """Interactive menu untuk remove plugin."""
    installed = get_installed_plugins(install_dir)

    _header("Remove Plugins", "🗑")

    if not installed:
        print("  Tidak ada plugin yang terinstall.\n")
        return

    pid_list = list(installed)
    print("  Plugin yang terinstall:\n")
    for i, pid in enumerate(pid_list, 1):
        info = OFFICIAL_PLUGINS.get(pid, {})
        print(f"  {i}. {info.get('label', pid)}")
        print(f"     {info.get('description', '')}\n")

    print("  Masukkan nomor plugin yang ingin dihapus (contoh: 1 2):")
    try:
        raw = input("  > ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n  Cancelled.")
        return

    if not raw:
        print("  Tidak ada yang dipilih.")
        return

    to_remove = []
    for token in raw.split():
        try:
            idx = int(token) - 1
            if 0 <= idx < len(pid_list):
                to_remove.append(pid_list[idx])
        except ValueError:
            pass

    if not to_remove:
        return

    print(f"\n  Plugin yang akan dihapus:")
    for pid in to_remove:
        print(f"    • {OFFICIAL_PLUGINS.get(pid, {}).get('label', pid)}")

    if not _confirm("\n  Lanjutkan?", default=False):
        print("  Dibatalkan.")
        return

    for pid in to_remove:
        _plugin_remove_direct(install_dir, pid, cfg, OFFICIAL_PLUGINS,
                               lambda d, p: (install_dir / "plugins" / OFFICIAL_PLUGINS.get(p, {}).get("file", "")).exists())
    print("\n  Restart bot: simplecontext-bot start\n")


def _plugin_remove_direct(install_dir, plugin_id, cfg, OFFICIAL_PLUGINS, check_plugin):
    info     = OFFICIAL_PLUGINS.get(plugin_id, {})
    filepath = install_dir / "plugins" / info.get("file", "")
    if filepath.exists():
        filepath.unlink()
    installed = cfg.get("plugins.installed", [])
    if plugin_id in installed:
        installed.remove(plugin_id)
    cfg.set_value("plugins.installed", installed)
    print(f"  ✅ Plugin '{info.get('label', plugin_id)}' dihapus.")



def cmd_set(args):
    """Ubah satu nilai config tanpa harus setup ulang."""
    from . import config as cfg

    key   = args.key
    value = args.value

    # Validasi key yang diizinkan
    allowed = {
        "telegram.token":      "Telegram Bot Token",
        "llm.provider":        "LLM Provider (gemini|openai|ollama)",
        "llm.model":           "LLM Model name",
        "llm.api_key":         "LLM API Key",
        "llm.base_url":        "LLM Base URL (untuk ollama)",
        "simplecontext.default_agent": "Default agent name",
        "bot.debug":           "Debug mode (true|false)",
        "bot.memory_limit":    "Memory limit (integer)",
        "bot.max_tokens":      "Max tokens per LLM response (default: 2048)",
    }

    if key not in allowed:
        print(f"❌ Key tidak dikenal: '{key}'")
        print("\n  Keys yang bisa diubah:")
        for k, desc in allowed.items():
            current = cfg.get(k, "—")
            # Sensor token/key
            if "token" in k or "key" in k or "api" in k:
                display = "****" if current and current != "—" else "—"
            else:
                display = str(current)
            print(f"    {k:<35} {desc}")
            print(f"    {'':35} Current: {display}")
        return

    # Konversi tipe
    actual_value = value
    if key in ("bot.debug",):
        actual_value = value.lower() in ("true", "1", "yes")
    elif key in ("bot.memory_limit", "bot.max_tokens"):
        try:
            actual_value = int(value)
        except ValueError:
            print(f"❌ Nilai harus berupa angka untuk key '{key}'")
            return

    cfg.set_value(key, actual_value)

    # Sensor saat display
    display = "****" if ("token" in key or "key" in key or "api" in key) else str(actual_value)
    print(f"✅ {key} = {display}")
    print(f"   ({allowed[key]})")

    if key == "telegram.token":
        print("\n   Restart bot untuk menerapkan: simplecontext-bot start")
    elif key.startswith("llm."):
        print("\n   Restart bot untuk menerapkan: simplecontext-bot start")

def cmd_dashboard(args):
    """
    Dashboard ringkasan lengkap — status, agents, plugins, config, usage.
    Satu command untuk lihat semua kondisi bot sekarang.
    """
    from . import config as cfg
    from .installer import (
        check_engine, check_agents, get_installed_agents,
        get_installed_plugins, OFFICIAL_PLUGINS,
    )
    from .config import DEFAULT_DIR
    from pathlib import Path
    import os

    install_dir = Path(cfg.get("install_dir", str(DEFAULT_DIR)))

    width = 56
    print("\n" + "═" * width)
    print("  🧠  SimpleContext-Bot — Dashboard")
    print("═" * width)

    # ── System ────────────────────────────────────────────
    print("\n  📦 System\n  " + "─" * 40)

    engine_ok = check_engine(install_dir)
    print(f"  Engine       {'✅ Installed' if engine_ok else '❌ Missing'}")

    db_path = Path(cfg.get("simplecontext.db_path", ""))
    if db_path.exists():
        db_size = db_path.stat().st_size / 1024
        print(f"  Database     ✅ {db_size:.1f} KB  ({db_path})")
    else:
        print(f"  Database     ❌ Not found")

    # ── Agents ────────────────────────────────────────────
    print("\n  🤖 Agents\n  " + "─" * 40)
    agents = get_installed_agents(install_dir)
    if agents:
        print(f"  Installed    {len(agents)} agents")
        agents_dir = install_dir / "agents"
        for name in sorted(agents):
            yaml_path = agents_dir / f"{name}.yaml"
            desc = ""
            try:
                for line in open(yaml_path).read().splitlines():
                    if line.startswith("description:"):
                        desc = line.split(":", 1)[1].strip()[:40]
                        break
            except Exception:
                pass
            print(f"    • {name:<18} {desc}")
    else:
        print("  Installed    ❌ None")

    # ── Plugins ───────────────────────────────────────────
    print("\n  🔌 Plugins\n  " + "─" * 40)
    installed_plugins = get_installed_plugins(install_dir)
    if installed_plugins:
        for pid in installed_plugins:
            info     = OFFICIAL_PLUGINS.get(pid, {})
            label    = info.get("label", pid)
            filename = info.get("file", "")
            size     = ""
            fp       = install_dir / "plugins" / filename
            if fp.exists():
                size = f"  ({fp.stat().st_size // 1024} KB)"
            print(f"    ✅ {label}{size}")
    else:
        print("  No plugins installed.")
        print("  Run: simplecontext-bot plugins install")

    # ── LLM ───────────────────────────────────────────────
    print("\n  🤖 LLM Configuration\n  " + "─" * 40)
    provider = cfg.get("llm.provider", "—")
    model    = cfg.get("llm.model", "—")
    api_key  = cfg.get("llm.api_key", "")
    key_str  = f"{'*' * 8}{api_key[-4:]}" if len(api_key) > 4 else ("configured" if api_key else "❌ Missing")
    print(f"  Provider     {provider}")
    print(f"  Model        {model}")
    print(f"  API Key      {key_str}")

    # ── Telegram ──────────────────────────────────────────
    print("\n  📱 Telegram\n  " + "─" * 40)
    token = cfg.get("telegram.token", "")
    tok_str = f"{'*' * 10}{token[-6:]}" if len(token) > 6 else ("configured" if token else "❌ Missing")
    print(f"  Token        {tok_str}")

    # ── Bot Config ────────────────────────────────────────
    print("\n  ⚙️  Bot Config\n  " + "─" * 40)
    print(f"  Install dir  {install_dir}")
    print(f"  Default agent {cfg.get('simplecontext.default_agent', 'general')}")
    print(f"  Memory limit  {cfg.get('bot.memory_limit', 20)} messages")
    print(f"  Hot reload    {'✅ On' if cfg.get('simplecontext.hot_reload', True) else '❌ Off'}")
    print(f"  Debug mode    {'✅ On' if cfg.get('bot.debug', False) else 'Off'}")

    # ── Quick Actions ─────────────────────────────────────
    print("\n  " + "─" * 40)
    print("  Quick actions:")
    print("  simplecontext-bot start               — start bot")
    print("  simplecontext-bot plugins install     — add plugins")
    print("  simplecontext-bot update              — update engine + agents")
    print("  simplecontext-bot status --test       — test LLM connection")
    print()
    print("═" * width + "\n")


# ── Main ──────────────────────────────────────────────────



def cmd_set(args):
    """Ubah satu nilai config tanpa harus setup ulang."""
    from . import config as cfg

    key   = args.key
    value = args.value

    # Validasi key yang diizinkan
    allowed = {
        "telegram.token":      "Telegram Bot Token",
        "llm.provider":        "LLM Provider (gemini|openai|ollama)",
        "llm.model":           "LLM Model name",
        "llm.api_key":         "LLM API Key",
        "llm.base_url":        "LLM Base URL (untuk ollama)",
        "simplecontext.default_agent": "Default agent name",
        "bot.debug":           "Debug mode (true|false)",
        "bot.memory_limit":    "Memory limit (integer)",
        "bot.max_tokens":      "Max tokens per LLM response (default: 2048)",
    }

    if key not in allowed:
        print(f"❌ Key tidak dikenal: '{key}'")
        print("\n  Keys yang bisa diubah:")
        for k, desc in allowed.items():
            current = cfg.get(k, "—")
            # Sensor token/key
            if "token" in k or "key" in k or "api" in k:
                display = "****" if current and current != "—" else "—"
            else:
                display = str(current)
            print(f"    {k:<35} {desc}")
            print(f"    {'':35} Current: {display}")
        return

    # Konversi tipe
    actual_value = value
    if key in ("bot.debug",):
        actual_value = value.lower() in ("true", "1", "yes")
    elif key in ("bot.memory_limit", "bot.max_tokens"):
        try:
            actual_value = int(value)
        except ValueError:
            print(f"❌ Nilai harus berupa angka untuk key '{key}'")
            return

    cfg.set_value(key, actual_value)

    # Sensor saat display
    display = "****" if ("token" in key or "key" in key or "api" in key) else str(actual_value)
    print(f"✅ {key} = {display}")
    print(f"   ({allowed[key]})")

    if key == "telegram.token":
        print("\n   Restart bot untuk menerapkan: simplecontext-bot start")
    elif key.startswith("llm."):
        print("\n   Restart bot untuk menerapkan: simplecontext-bot start")

def cmd_dashboard(args):
    """Tampilkan dashboard statistik bot."""
    from . import config as cfg
    from .installer import check_engine, check_agents, get_installed_agents, get_installed_plugins
    from .config import DEFAULT_DIR
    import sys, os

    install_dir  = Path(cfg.get("install_dir", str(DEFAULT_DIR)))
    engine_ok    = check_engine(install_dir)
    agents       = get_installed_agents(install_dir)
    plugins      = get_installed_plugins(install_dir)
    provider     = cfg.get("llm.provider", "—")
    model        = cfg.get("llm.model", "—")
    db_path      = Path(cfg.get("simplecontext.db_path", ""))
    token        = cfg.get("telegram.token", "")

    # DB size
    db_size = "—"
    if db_path.exists():
        size_bytes = db_path.stat().st_size
        if size_bytes > 1_048_576:
            db_size = f"{size_bytes / 1_048_576:.1f} MB"
        elif size_bytes > 1024:
            db_size = f"{size_bytes / 1024:.1f} KB"
        else:
            db_size = f"{size_bytes} B"

    # Ambil stats dari DB jika bisa
    users = messages = llm_calls = 0
    try:
        sys.path.insert(0, str(install_dir))
        from simplecontext import SimpleContext
        sc = SimpleContext(
            storage__backend = "sqlite",
            storage__path    = str(db_path),
            plugins__enabled = False,
        )
        stats    = sc.stats()
        users    = stats.get("total_users", 0)
        messages = stats.get("total_nodes", 0)
        sc.close()
    except Exception:
        pass

    sep = "─" * 50
    print(f"""
╔══════════════════════════════════════════════════╗
║         SimpleContext-Bot Dashboard              ║
╚══════════════════════════════════════════════════╝

  🔧 System
  {sep}
  Engine     : {"✅ Installed" if engine_ok else "❌ Not installed"}
  DB size    : {db_size}
  Telegram   : {"✅ Configured" if token else "❌ Not configured"}

  🤖 Agents & Plugins
  {sep}
  Agents     : {len(agents)} installed  ({", ".join(sorted(agents)[:5])}{"..." if len(agents) > 5 else ""})
  Plugins    : {len(plugins)} installed  ({", ".join(plugins) if plugins else "none"})

  🧠 LLM
  {sep}
  Provider   : {provider}
  Model      : {model}

  📊 Usage Stats
  {sep}
  Users      : {users}
  Nodes      : {messages}

  📁 Install dir : {install_dir}
""")

def main():
    parser = argparse.ArgumentParser(
        prog="simplecontext-bot",
        description="🧠 SimpleContext-Bot — AI Telegram Bot powered by SimpleContext",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.3.0")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # setup
    p = subparsers.add_parser("setup", help="Run setup wizard")
    p.set_defaults(func=cmd_setup)

    # start
    p = subparsers.add_parser("start", help="Start the bot")
    p.add_argument("--debug", action="store_true")
    p.set_defaults(func=cmd_start)

    # status
    p = subparsers.add_parser("status", help="Show bot status")
    p.add_argument("--test", action="store_true", help="Test LLM connection")
    p.set_defaults(func=cmd_status)

    # dashboard
    p = subparsers.add_parser("dashboard", help="Full dashboard — system, agents, plugins, config")
    p.set_defaults(func=cmd_dashboard)

    # agents
    p = subparsers.add_parser("agents", help="List installed agents")
    p.set_defaults(func=cmd_agents)

    # update
    p = subparsers.add_parser("update", help="Update engine, agents, dan plugins")
    p.add_argument("--engine-only",  action="store_true")
    p.add_argument("--agents-only",  action="store_true")
    p.add_argument("--plugins-only", action="store_true")
    p.set_defaults(func=cmd_update)

    # plugins
    p_plugins  = subparsers.add_parser("plugins", help="Manage plugins")
    p_plugins.set_defaults(func=cmd_plugins)
    plugin_sub = p_plugins.add_subparsers(dest="plugin_action")

    p_sub = plugin_sub.add_parser("list", help="List all plugins")
    p_sub.set_defaults(plugin_action="list")

    p_sub = plugin_sub.add_parser("install", help="Install plugin (interactive menu if no ID given)")
    p_sub.add_argument("plugin_id", nargs="?", help="Plugin ID (optional — omit for interactive menu)")
    p_sub.set_defaults(plugin_action="install")

    p_sub = plugin_sub.add_parser("remove", help="Remove plugin (interactive menu if no ID given)")
    p_sub.add_argument("plugin_id", nargs="?", help="Plugin ID (optional — omit for interactive menu)")
    p_sub.set_defaults(plugin_action="remove")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "plugins" and not getattr(args, "plugin_action", None):
        args.plugin_action = "list"

    args.func(args)


if __name__ == "__main__":
    main()
