"""
bot.py — Telegram Bot v1.1
Generic, zero-touch bot yang menggunakan SimpleContext sebagai otak.
v1.1: Plugin ecosystem integration — /plugins, /semantic, auto-load plugins dari config.
"""

import sys
import logging
from pathlib import Path
from . import config as cfg
from . import llm

logger = logging.getLogger(__name__)


def _load_simplecontext():
    """Load SimpleContext dari install directory."""
    install_dir = Path(cfg.get("install_dir"))
    engine_dir  = install_dir

    if str(engine_dir) not in sys.path:
        sys.path.insert(0, str(engine_dir))

    try:
        from simplecontext import SimpleContext
        return SimpleContext
    except ImportError:
        logger.error("SimpleContext not found. Run: simplecontext-bot setup")
        return None


def _load_plugins(sc, install_dir: Path):
    """
    Load plugin yang sudah diinstall via setup wizard ke SimpleContext instance.
    Plugin diambil dari install_dir/plugins/ dan dikonfigurasi via config.json.
    """
    plugins_dir     = install_dir / "plugins"
    installed_ids   = cfg.get("plugins.installed", [])
    plugin_configs  = cfg.get("plugins.configs", {})

    if not installed_ids or not plugins_dir.exists():
        return 0

    # Pastikan plugins_dir masuk sys.path agar plugin bisa import simplecontext
    if str(plugins_dir) not in sys.path:
        sys.path.insert(0, str(plugins_dir))

    loaded = 0
    for plugin_id in installed_ids:
        from .installer import OFFICIAL_PLUGINS
        info = OFFICIAL_PLUGINS.get(plugin_id)
        if not info:
            continue

        plugin_file = plugins_dir / info["file"]
        if not plugin_file.exists():
            logger.warning(f"Plugin file tidak ditemukan: {plugin_file}")
            continue

        try:
            import importlib.util
            spec   = importlib.util.spec_from_file_location(
                f"sc_plugin_{plugin_id.replace('-', '_')}", plugin_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Cari class BasePlugin
            from simplecontext.plugins.base import BasePlugin
            plugin_cls = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type)
                        and issubclass(attr, BasePlugin)
                        and attr is not BasePlugin
                        and getattr(attr, "name", "")):
                    plugin_cls = attr
                    break

            if not plugin_cls:
                logger.warning(f"Tidak ada BasePlugin class di {plugin_file.name}")
                continue

            plugin_cfg = plugin_configs.get(plugin_id, info.get("config", {}))
            sc.use(plugin_cls(config=plugin_cfg))
            logger.info(f"✅ Plugin loaded: {plugin_cls.name} v{plugin_cls.version}")
            loaded += 1

        except Exception as e:
            logger.warning(f"Gagal load plugin '{plugin_id}': {e}")

    return loaded


def run():
    """Jalankan Telegram bot."""
    token = cfg.get("telegram.token", "")
    if not token:
        print("❌ Telegram token not configured. Run: simplecontext-bot setup")
        sys.exit(1)

    try:
        from telegram import Update
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

    sc = SimpleContext(
        storage__backend         = "sqlite",
        storage__path            = cfg.get("simplecontext.db_path"),
        agents__folder           = cfg.get("simplecontext.agents_dir"),
        agents__hot_reload       = cfg.get("simplecontext.hot_reload", True),
        agents__default          = cfg.get("simplecontext.default_agent", "general"),
        plugins__enabled         = False,   # kita manage sendiri via sc.use()
        plugins__folder          = str(install_dir / "plugins"),
        memory__default_limit    = cfg.get("bot.memory_limit", 20),
        debug__retrieval         = cfg.get("bot.debug", False),
    )

    # Load plugins yang terinstall
    plugin_count = _load_plugins(sc, install_dir)
    agents = sc._registry.names()
    logger.info(
        f"✅ SimpleContext ready — {len(agents)} agents, {plugin_count} plugins"
    )

    # ── Helpers ───────────────────────────────────────────

    def _escape(text: str) -> str:
        """Escape karakter MarkdownV2."""
        for ch in r"_*[]()~`>#+-=|{}.!":
            text = text.replace(ch, f"\\{ch}")
        return text

    # ── Handlers ──────────────────────────────────────────

    async def cmd_start(update: Update, ctx):
        user = update.effective_user
        mem  = sc.memory(user.id)
        mem.remember("name", user.first_name)
        if user.username:
            mem.remember("username", f"@{user.username}")

        agents_list = "\n".join(f"  • `{a}`" for a in agents)

        # Cek apakah ada plugin aktif untuk ditampilkan
        from .installer import OFFICIAL_PLUGINS, get_installed_plugins
        installed = get_installed_plugins(install_dir)
        plugin_line = ""
        if installed:
            labels = ", ".join(OFFICIAL_PLUGINS[p]["label"] for p in installed if p in OFFICIAL_PLUGINS)
            plugin_line = f"\n\n🔌 *Active plugins:* {labels}"

        await update.message.reply_text(
            f"👋 Hello *{user.first_name}*\\!\n\n"
            f"I'm powered by *SimpleContext* — an AI brain with memory\\.\n\n"
            f"🤖 *Available agents:*\n{agents_list}"
            f"{plugin_line}\n\n"
            f"I'll auto\\-select the best agent for each message\\.\n"
            f"Or use /agent \\<name\\> to choose manually\\.",
            parse_mode="MarkdownV2"
        )

    async def cmd_help(update: Update, ctx):
        await update.message.reply_text(
            "📖 *Commands:*\n\n"
            "/start — Welcome message\n"
            "/agent \\<name\\> — Set agent manually\n"
            "/agent auto — Back to auto\\-routing\n"
            "/agents — List all available agents\n"
            "/clear — Clear conversation history\n"
            "/status — Show current status\n"
            "/memory — Show your saved profile\n"
            "/plugins — List installed plugins\n"
            "/semantic \\<query\\> — Search memory by meaning\n",
            parse_mode="MarkdownV2"
        )

    async def cmd_agents(update: Update, ctx):
        lines = ["🤖 *Available Agents:*\n"]
        for name in agents:
            agent = sc._registry.get(name)
            desc  = agent.description if agent else ""
            lines.append(f"• *{name}* — {desc}")
        lines.append("\n_Use /agent \\<name\\> to select one_")
        await update.message.reply_text(
            "\n".join(lines), parse_mode="Markdown"
        )

    async def cmd_agent(update: Update, ctx):
        uid  = update.effective_user.id
        args = ctx.args

        if not args:
            current = sc.memory(uid).recall("preferred_agent", "auto")
            await update.message.reply_text(
                f"Current agent: `{current}`\n"
                f"Use `/agent <n>` or `/agent auto`",
                parse_mode="Markdown"
            )
            return

        name = args[0].lower()
        if name == "auto":
            sc.router.clear_user_agent(uid)
            await update.message.reply_text("✅ Back to *auto-routing*.", parse_mode="Markdown")
        elif name in agents:
            sc.router.set_user_agent(uid, name)
            await update.message.reply_text(
                f"✅ Agent set to *{name}*.", parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"❌ Agent `{name}` not found.\n"
                f"Available: {', '.join(f'`{a}`' for a in agents)}",
                parse_mode="Markdown"
            )

    async def cmd_clear(update: Update, ctx):
        sc.memory(update.effective_user.id).clear()
        await update.message.reply_text(
            "🗑 Conversation cleared\\. Profile kept\\.",
            parse_mode="MarkdownV2"
        )

    async def cmd_status(update: Update, ctx):
        uid    = update.effective_user.id
        mem    = sc.memory(uid)
        result = sc.router.route(uid, "")
        from .installer import get_installed_plugins, OFFICIAL_PLUGINS
        installed = get_installed_plugins(install_dir)
        plugin_str = (
            ", ".join(OFFICIAL_PLUGINS[p]["label"] for p in installed if p in OFFICIAL_PLUGINS)
            if installed else "None"
        )
        await update.message.reply_text(
            f"📊 *Status*\n\n"
            f"🤖 Agent: `{result.agent_id}`\n"
            f"💬 Messages: `{mem.count()}`\n"
            f"🧠 Agents loaded: `{len(agents)}`\n"
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
        await update.message.reply_text(
            "\n".join(lines), parse_mode="Markdown"
        )

    async def cmd_plugins(update: Update, ctx):
        """Tampilkan daftar plugin aktif dan yang tersedia."""
        from .installer import OFFICIAL_PLUGINS, get_installed_plugins
        installed = get_installed_plugins(install_dir)

        lines = ["🔌 *Plugin Ecosystem*\n"]

        if installed:
            lines.append("*Active plugins:*")
            for pid in installed:
                info = OFFICIAL_PLUGINS.get(pid, {})
                lines.append(f"  ✅ *{info.get('label', pid)}* — {info.get('description', '')}")
        else:
            lines.append("_No plugins installed._")

        available = [pid for pid in OFFICIAL_PLUGINS if pid not in installed]
        if available:
            lines.append("\n*Available to install:*")
            for pid in available:
                info = OFFICIAL_PLUGINS[pid]
                lines.append(
                    f"  ➕ *{info['label']}* — {info['description']}\n"
                    f"     `simplecontext-bot plugins install {pid}`"
                )
        else:
            lines.append("\n_All available plugins are installed!_ 🎉")

        lines.append(
            "\n📖 More plugins: "
            "[SimpleContext\\-Plugin](https://github.com/zacxyonly/SimpleContext-Plugin)"
        )

        await update.message.reply_text(
            "\n".join(lines), parse_mode="Markdown"
        )

    async def cmd_semantic(update: Update, ctx):
        """
        Demo vector search — cari memory berdasarkan makna.
        Usage: /semantic <query>
        Requires: vector-search plugin terinstall.
        """
        uid  = update.effective_user.id
        args = ctx.args
        query = " ".join(args).strip() if args else ""

        if not query:
            await update.message.reply_text(
                "🔍 *Semantic Memory Search*\n\n"
                "Usage: `/semantic <query>`\n\n"
                "Contoh:\n"
                "  `/semantic python error`\n"
                "  `/semantic liburan pantai`\n\n"
                "_Mencari memory berdasarkan makna, bukan kata persis._",
                parse_mode="Markdown"
            )
            return

        # Cek plugin tersedia
        vector_plugin = sc._plugins.get("vector_search_plugin")
        if not vector_plugin:
            await update.message.reply_text(
                "❌ *Vector Search plugin tidak aktif.*\n\n"
                "Install dulu:\n"
                "`simplecontext-bot plugins install vector-search`\n\n"
                "Atau jalankan ulang setup:\n"
                "`simplecontext-bot setup`",
                parse_mode="Markdown"
            )
            return

        await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

        try:
            hits = vector_plugin._search(str(uid), query)
        except Exception as e:
            await update.message.reply_text(f"❌ Search error: {e}")
            return

        if not hits:
            await update.message.reply_text(
                f"🔍 No results for: *{query}*\n\n"
                "_Vector index mungkin masih kosong. Mulai chatting dulu agar memory terisi._",
                parse_mode="Markdown"
            )
            return

        lines = [f"🔍 *Semantic search:* `{query}`\n"]
        for i, hit in enumerate(hits, 1):
            pct        = int(hit["score"] * 100)
            tier_label = hit["tier"].capitalize() if hit["tier"] else "Memory"
            bar        = "█" * (pct // 20) + "░" * (5 - pct // 20)
            lines.append(
                f"{i}. [{tier_label} | {bar} {pct}%]\n"
                f"   _{hit['content'][:120]}_"
            )

        await update.message.reply_text(
            "\n\n".join(lines), parse_mode="Markdown"
        )

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

        reply = llm.call(messages, max_tokens=1024)

        chain_rule = result.should_chain(text)
        if chain_rule and not reply.startswith("❌"):
            await ctx.bot.send_chat_action(update.effective_chat.id, "typing")
            result2   = sc.router.chain(uid, text, reply, chain_rule,
                                        from_agent_id=result.agent_id)
            messages2 = sc.prepare_messages(uid, text, result2)
            reply     = llm.call(messages2, max_tokens=1024)
            reply     = sc.process_response(uid, text, reply, result2,
                                            chain_from=result.agent_id)
        else:
            reply = sc.process_response(uid, text, reply, result)

        try:
            await update.message.reply_text(reply, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(reply)

    # ── Build App ──────────────────────────────────────────

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("help",     cmd_help))
    app.add_handler(CommandHandler("agents",   cmd_agents))
    app.add_handler(CommandHandler("agent",    cmd_agent))
    app.add_handler(CommandHandler("clear",    cmd_clear))
    app.add_handler(CommandHandler("status",   cmd_status))
    app.add_handler(CommandHandler("memory",   cmd_memory))
    app.add_handler(CommandHandler("plugins",  cmd_plugins))
    app.add_handler(CommandHandler("semantic", cmd_semantic))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot is running... (Ctrl+C to stop)")
    app.run_polling(drop_pending_updates=True)
