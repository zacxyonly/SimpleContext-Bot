"""
bot.py — Telegram Bot v1.2
Dynamic plugin system:
  - Auto-scan semua .py di plugins/ folder (termasuk plugin komunitas)
  - Plugin bisa declare BOT_COMMANDS untuk auto-register command ke Telegram
  - /plugins selalu akurat: baca dari sc._plugins, bukan registry hardcoded
"""

import sys
import logging
import importlib.util
from pathlib import Path
from . import config as cfg
from . import llm

logger = logging.getLogger(__name__)

# ── Message Formatting Helpers ────────────────────────────────────────────────

_TG_MAX_LEN = 4096


def _clean_md(text: str) -> str:
    """Bersihkan Markdown agar aman untuk Telegram parse_mode=Markdown."""
    import re
    # "* item" gaya Gemini → "• item"
    text = re.sub(r"(?m)^\*\s+", "• ", text)
    # Hapus ** yang tidak dipasangkan
    if text.count("**") % 2 != 0:
        last = text.rfind("**")
        text = text[:last] + text[last + 2:]
    return text


def _split_msg(text: str, max_len: int = _TG_MAX_LEN) -> list:
    """Split teks panjang menjadi chunk yang aman untuk Telegram."""
    if len(text) <= max_len:
        return [text]
    parts = []
    remaining = text
    while len(remaining) > max_len:
        chunk = remaining[:max_len]
        cut = max_len
        for sep, off in [("\n\n", 2), ("\n", 1), (". ", 2), ("! ", 2), ("? ", 2)]:
            pos = chunk.rfind(sep)
            if pos > max_len // 2:
                cut = pos + off
                break
        parts.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    if remaining:
        parts.append(remaining)
    return parts


async def _send_reply(update, text: str, parse_mode: str = "Markdown"):
    """Kirim reply: clean → split → fallback plain jika Markdown error."""
    text   = _clean_md(text)
    chunks = _split_msg(text)
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode=parse_mode)
        except Exception:
            try:
                await update.message.reply_text(chunk)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to send: {e}")



def _load_simplecontext():
    install_dir = Path(cfg.get("install_dir"))
    if str(install_dir) not in sys.path:
        sys.path.insert(0, str(install_dir))
    try:
        from simplecontext import SimpleContext
        return SimpleContext
    except ImportError:
        logger.error("SimpleContext not found. Run: simplecontext-bot setup")
        return None


# ── Plugin Loader ─────────────────────────────────────────────────────────────

def _scan_plugin_files(plugins_dir: Path) -> list[Path]:
    """
    Scan semua file .py di plugins_dir.
    Tidak tergantung OFFICIAL_PLUGINS — plugin komunitas yang di-drop manual
    juga terdeteksi otomatis.
    """
    if not plugins_dir.exists():
        return []
    return [f for f in plugins_dir.glob("*.py") if not f.name.startswith("_")]


def _load_plugin_class(plugin_file: Path):
    """
    Load satu file plugin, return (plugin_class, module) atau (None, None).
    Cari class pertama yang mewarisi BasePlugin dengan atribut name.
    """
    try:
        from simplecontext.plugins.base import BasePlugin
    except ImportError:
        return None, None

    try:
        module_name = f"sc_plugin_{plugin_file.stem}"
        spec   = importlib.util.spec_from_file_location(module_name, plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type)
                    and issubclass(attr, BasePlugin)
                    and attr is not BasePlugin
                    and getattr(attr, "name", "")):
                return attr, module

        logger.warning(f"Tidak ada BasePlugin class di {plugin_file.name}")
        return None, None

    except Exception as e:
        logger.warning(f"Gagal load plugin '{plugin_file.name}': {e}")
        return None, None


def _load_all_plugins(sc, install_dir: Path) -> dict:
    """
    Auto-scan dan load semua plugin dari install_dir/plugins/.
    Tidak bergantung config.json installed list — semua .py ter-load otomatis.

    Return: dict { plugin_name: plugin_instance }
    """
    plugins_dir    = install_dir / "plugins"
    plugin_files   = _scan_plugin_files(plugins_dir)
    plugin_configs = cfg.get("plugins.configs", {})

    if not plugin_files:
        return {}

    if str(plugins_dir) not in sys.path:
        sys.path.insert(0, str(plugins_dir))

    loaded = {}
    for plugin_file in sorted(plugin_files):
        plugin_cls, _ = _load_plugin_class(plugin_file)
        if not plugin_cls:
            continue

        plugin_name = plugin_cls.name

        # Cari config: dari config.json (keyed by plugin_id atau plugin_name)
        # Fallback ke empty dict — plugin tetap load dengan default config-nya
        plugin_cfg = (
            plugin_configs.get(plugin_name)
            or plugin_configs.get(plugin_file.stem)
            or {}
        )

        try:
            sc.use(plugin_cls(config=plugin_cfg))
            loaded[plugin_name] = sc._plugins.get(plugin_name)
            logger.info(
                f"✅ Plugin loaded: {plugin_name} v{plugin_cls.version}"
                + (f" (BOT_COMMANDS: {list(plugin_cls.BOT_COMMANDS.keys())})"
                   if getattr(plugin_cls, "BOT_COMMANDS", None) else "")
            )
        except Exception as e:
            logger.warning(f"Gagal register plugin '{plugin_name}': {e}")

    return loaded


# ── Dynamic Command Registration ─────────────────────────────────────────────

def _collect_app_commands(sc) -> dict:
    """
    Kumpulkan semua app_commands dari plugin via loader.get_all_app_commands().
    Menggunakan kontrak resmi BasePlugin v4 — bukan convention ad-hoc.
    Return: { "command_name": {...cmd_info, "plugin": plugin_instance} }
    """
    commands = sc._plugins.get_all_app_commands()
    for cmd_name, cmd_info in commands.items():
        plugin_name = cmd_info["plugin"].name
        logger.info(f"  ↳ App command: /{cmd_name} (dari {plugin_name})")
    return commands


def _make_dynamic_handler(sc, cmd_name: str):
    """
    Buat async Telegram handler untuk satu app_command.
    Eksekusi via sc._plugins.fire_app_command() — routing ditangani core,
    bukan bot. Handler plugin cukup terima AppCommandContext.
    """
    async def handler(update, ctx):
        from simplecontext.plugins.base import AppCommandContext

        tg_ctx = AppCommandContext.create(
            command  = cmd_name,
            user_id  = str(update.effective_user.id),
            args     = ctx.args or [],
            platform = "telegram",
            raw      = update,
            sc       = sc,
        )

        await ctx.bot.send_chat_action(update.effective_chat.id, "typing")
        try:
            result = await sc._plugins.fire_app_command(tg_ctx)
            if result:
                try:
                    await update.message.reply_text(result, parse_mode="Markdown")
                except Exception:
                    await update.message.reply_text(result)
            else:
                await update.message.reply_text(
                    f"⚠️ Command `/{cmd_name}` tidak menghasilkan response.",
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Error di app_command /{cmd_name}: {e}")
            await update.message.reply_text(f"❌ Error: {e}")

    handler.__name__ = f"plugin_cmd_{cmd_name}"
    return handler


# ── Bot Runner ────────────────────────────────────────────────────────────────

def run():
    token = cfg.get("telegram.token", "")
    if not token:
        print("❌ Telegram token not configured. Run: simplecontext-bot setup")
        sys.exit(1)

    try:
        from telegram import Update, BotCommand
        from telegram.ext import (
            ApplicationBuilder, CommandHandler,
            MessageHandler, filters,
        )
    except ImportError:
        print("❌ python-telegram-bot not installed.")
        print("   Run: pip install python-telegram-bot")
        sys.exit(1)

    SimpleContext = _load_simplecontext()
    if not SimpleContext:
        print("❌ SimpleContext engine not found. Run: simplecontext-bot setup")
        sys.exit(1)

    install_dir = Path(cfg.get("install_dir"))

    max_tokens = cfg.get("bot.max_tokens", 2048)

    sc = SimpleContext(
        storage__backend      = "sqlite",
        storage__path         = cfg.get("simplecontext.db_path"),
        agents__folder        = cfg.get("simplecontext.agents_dir"),
        agents__hot_reload    = cfg.get("simplecontext.hot_reload", True),
        agents__default       = cfg.get("simplecontext.default_agent", "general"),
        plugins__enabled      = False,
        plugins__folder       = str(install_dir / "plugins"),
        memory__default_limit = cfg.get("bot.memory_limit", 20),
        debug__retrieval      = cfg.get("bot.debug", False),
    )

    # ── Load semua plugin (auto-scan, tidak tergantung registry) ──────────────
    loaded_plugins  = _load_all_plugins(sc, install_dir)
    dynamic_commands = _collect_app_commands(sc)

    # Inject app_info ke semua plugin — mereka bisa tahu platform & versi bot
    sc._plugins.set_app_info({"platform": "telegram", "version": "1.2.0"})

    agents = sc._registry.names()
    logger.info(
        f"✅ Bot ready — {len(agents)} agents, "
        f"{len(loaded_plugins)} plugins, "
        f"{len(dynamic_commands)} plugin commands"
    )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _plugin_summary_lines() -> list[str]:
        """Buat daftar ringkasan plugin yang ter-load untuk ditampilkan di bot."""
        lines = []
        all_plugins = sc._plugins.all()
        if not all_plugins:
            return ["_No plugins active._"]
        for p in all_plugins:
            cmds = p.get_app_commands()
            cmd_str = ""
            if cmds:
                cmd_str = "  ·  commands: " + ", ".join(f"`/{c}`" for c in cmds)
            lines.append(f"  ✅ *{p.name}* v{p.version} — {p.description}{cmd_str}")
        return lines

    # ── Static Handlers ───────────────────────────────────────────────────────

    async def cmd_start(update: Update, ctx):
        user = update.effective_user
        mem  = sc.memory(user.id)
        mem.remember("name", user.first_name)
        if user.username:
            mem.remember("username", f"@{user.username}")

        agents_list  = "\n".join(f"  • `{a}`" for a in agents)
        plugin_lines = _plugin_summary_lines()
        plugin_block = ""
        if loaded_plugins:
            plugin_block = "\n\n🔌 *Active plugins:*\n" + "\n".join(plugin_lines)

        await update.message.reply_text(
            f"👋 Hello *{user.first_name}*!\n\n"
            f"I'm powered by *SimpleContext* — an AI brain with memory.\n\n"
            f"🤖 *Available agents:*\n{agents_list}"
            f"{plugin_block}\n\n"
            f"Use /plugins to see plugin details.",
            parse_mode="Markdown"
        )

    async def cmd_help(update: Update, ctx):
        static_cmds = (
            "/start — Welcome message\n"
            "/agents — List all agents\n"
            "/agent <name> — Switch agent\n"
            "/agent auto — Back to auto-routing\n"
            "/clear — Clear conversation history\n"
            "/status — Current status\n"
            "/memory — Your saved profile\n"
            "/plugins — Plugin details & available commands\n"
        )
        dynamic_cmd_lines = ""
        if dynamic_commands:
            dynamic_cmd_lines = "\n*Plugin Commands:*\n"
            for cmd_name, info in dynamic_commands.items():
                usage = info.get("usage", f"/{cmd_name}")
                desc  = info.get("description", "")
                dynamic_cmd_lines += f"/{cmd_name} — {desc}\n"
                if usage != f"/{cmd_name}":
                    dynamic_cmd_lines += f"  Usage: `{usage}`\n"

        await update.message.reply_text(
            "📖 *Commands:*\n\n" + static_cmds + dynamic_cmd_lines,
            parse_mode="Markdown"
        )

    async def cmd_agents(update: Update, ctx):
        lines = ["🤖 *Available Agents:*\n"]
        for name in agents:
            agent = sc._registry.get(name)
            desc  = agent.description if agent else ""
            lines.append(f"• *{name}* — {desc}")
        lines.append("\n_Use /agent \\<name\\> to select one_")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def cmd_agent(update: Update, ctx):
        uid  = update.effective_user.id
        args = ctx.args
        if not args:
            current = sc.memory(uid).recall("preferred_agent", "auto")
            await update.message.reply_text(
                f"Current agent: `{current}`\nUse `/agent <n>` or `/agent auto`",
                parse_mode="Markdown"
            )
            return
        name = args[0].lower()
        if name == "auto":
            sc.router.clear_user_agent(uid)
            await update.message.reply_text("✅ Back to *auto-routing*.", parse_mode="Markdown")
        elif name in agents:
            sc.router.set_user_agent(uid, name)
            await update.message.reply_text(f"✅ Agent set to *{name}*.", parse_mode="Markdown")
        else:
            await update.message.reply_text(
                f"❌ Agent `{name}` not found.\nAvailable: {', '.join(f'`{a}`' for a in agents)}",
                parse_mode="Markdown"
            )

    async def cmd_clear(update: Update, ctx):
        sc.memory(update.effective_user.id).clear()
        await update.message.reply_text("🗑 Conversation cleared. Profile kept.", parse_mode="Markdown")

    async def cmd_status(update: Update, ctx):
        uid    = update.effective_user.id
        mem    = sc.memory(uid)
        result = sc.router.route(uid, "")
        all_p  = sc._plugins.all()
        plugin_str = ", ".join(p.name for p in all_p) if all_p else "None"
        await update.message.reply_text(
            f"📊 *Status*\n\n"
            f"🤖 Agent: `{result.agent_id}`\n"
            f"💬 Messages: `{mem.count()}`\n"
            f"🧠 Agents: `{len(agents)}`\n"
            f"🔌 Plugins: `{plugin_str}`",
            parse_mode="Markdown"
        )

    async def cmd_memory(update: Update, ctx):
        uid     = update.effective_user.id
        profile = sc.memory(uid).get_profile()
        display = {k: v for k, v in profile.items()
                   if not k.startswith("_") and k != "preferred_agent"}
        if not display:
            await update.message.reply_text("📝 No profile data saved yet.")
            return
        lines = ["📝 *Your Profile:*\n"]
        for k, v in display.items():
            lines.append(f"• *{k}*: {v}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def cmd_plugins(update: Update, ctx):
        """
        Tampilkan semua plugin aktif (baca dari sc._plugins, bukan registry hardcoded).
        Plugin komunitas yang di-drop manual ke plugins/ juga muncul di sini.
        """
        lines = ["🔌 *Active Plugins*\n"]
        all_p = sc._plugins.all()

        if not all_p:
            lines.append("_No plugins loaded._\n")
            lines.append("Drop plugin `.py` ke folder `~/.simplecontext-bot/plugins/` dan restart bot.")
        else:
            for p in all_p:
                cmds = p.get_app_commands()
                lines.append(f"*{p.name}* v{p.version}")
                lines.append(f"  {p.description}")
                if cmds:
                    for cmd_name, cmd_info in cmds.items():
                        lines.append(f"  • `/{cmd_name}` — {cmd_info.get('description', '')}")
                        lines.append(f"    Usage: `{cmd_info.get('usage', '/' + cmd_name)}`")
                lines.append("")

        lines.append("📖 More plugins: [SimpleContext\\-Plugin](https://github.com/zacxyonly/SimpleContext-Plugin)")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def handle_message(update: Update, ctx):
        uid  = update.effective_user.id
        user = update.effective_user
        text = update.message.text

        mem = sc.memory(uid)
        if not mem.recall("name"):
            mem.remember("name", user.first_name)
            if user.username:
                mem.remember("username", f"@{user.username}")

        await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

        result   = sc.router.route(uid, text)
        messages = sc.prepare_messages(uid, text, result)
        logger.info(f"[{user.username or uid}] → agent={result.agent_id}")

        reply = llm.call(messages, max_tokens=max_tokens)

        chain_rule = result.should_chain(text)
        if chain_rule and not reply.startswith("❌"):
            await ctx.bot.send_chat_action(update.effective_chat.id, "typing")
            result2   = sc.router.chain(uid, text, reply, chain_rule,
                                        from_agent_id=result.agent_id)
            messages2 = sc.prepare_messages(uid, text, result2)
            reply     = llm.call(messages2, max_tokens=max_tokens)
            reply     = sc.process_response(uid, text, reply, result2,
                                            chain_from=result.agent_id)
        else:
            reply = sc.process_response(uid, text, reply, result)

        await _send_reply(update, reply)

    # ── Build & Register Handlers ─────────────────────────────────────────────

    app = ApplicationBuilder().token(token).build()

    # Static commands
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("agents",  cmd_agents))
    app.add_handler(CommandHandler("agent",   cmd_agent))
    app.add_handler(CommandHandler("clear",   cmd_clear))
    app.add_handler(CommandHandler("status",  cmd_status))
    app.add_handler(CommandHandler("memory",  cmd_memory))
    app.add_handler(CommandHandler("plugins", cmd_plugins))

    # Dynamic commands dari plugin (auto-register)
    for cmd_name, cmd_info in dynamic_commands.items():
        handler_fn = _make_dynamic_handler(sc, cmd_name)
        app.add_handler(CommandHandler(cmd_name, handler_fn))
        logger.info(f"  ↳ Telegram handler registered: /{cmd_name}")

    # Set bot commands list di Telegram (muncul di menu)
    async def post_init(application):
        static = [
            BotCommand("start",   "Welcome message"),
            BotCommand("help",    "Show all commands"),
            BotCommand("agents",  "List available agents"),
            BotCommand("agent",   "Switch agent"),
            BotCommand("clear",   "Clear conversation history"),
            BotCommand("status",  "Show current status"),
            BotCommand("memory",  "Show your saved profile"),
            BotCommand("plugins", "List active plugins & their commands"),
        ]
        plugin_cmds = [
            BotCommand(cmd_name, info.get("description", "")[:256])
            for cmd_name, info in dynamic_commands.items()
        ]
        await application.bot.set_my_commands(static + plugin_cmds)

    app.post_init = post_init

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"🚀 Bot is running — {len(loaded_plugins)} plugins, {len(dynamic_commands)} plugin commands")
    if dynamic_commands:
        print(f"   Plugin commands: {', '.join('/' + c for c in dynamic_commands)}")
    app.run_polling(drop_pending_updates=True)
