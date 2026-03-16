"""
bot.py — Telegram Bot
Generic, zero-touch bot yang menggunakan SimpleContext sebagai otak.
Semua kecerdasan ada di agents/*.yaml — bot ini tidak perlu diubah.
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
    # simplecontext/ ada di dalam install_dir
    # jadi install_dir yang harus masuk sys.path
    engine_dir  = install_dir

    if str(engine_dir) not in sys.path:
        sys.path.insert(0, str(engine_dir))

    try:
        from simplecontext import SimpleContext
        return SimpleContext
    except ImportError:
        logger.error("SimpleContext not found. Run: simplecontext-bot setup")
        return None


def run():
    """Jalankan Telegram bot."""
    token = cfg.get("telegram.token", "")
    if not token:
        print("❌ Telegram token not configured. Run: simplecontext-bot setup")
        sys.exit(1)

    # Load dependencies
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

    # Load SimpleContext
    SimpleContext = _load_simplecontext()
    if not SimpleContext:
        print("❌ SimpleContext engine not found. Run: simplecontext-bot setup")
        sys.exit(1)

    # Init SimpleContext
    install_dir = Path(cfg.get("install_dir"))
    sc = SimpleContext(
        storage__backend    = "sqlite",
        storage__path       = cfg.get("simplecontext.db_path"),
        agents__folder      = cfg.get("simplecontext.agents_dir"),
        agents__hot_reload  = cfg.get("simplecontext.hot_reload", True),
        agents__default     = cfg.get("simplecontext.default_agent", "general"),
        plugins__enabled    = False,
        memory__default_limit    = cfg.get("bot.memory_limit", 20),
        debug__retrieval    = cfg.get("bot.debug", False),
    )

    agents = sc._registry.names()
    logger.info(f"✅ SimpleContext ready — {len(agents)} agents: {agents}")

    # ── Handlers ──────────────────────────────────────────

    async def cmd_start(update: Update, ctx):
        user = update.effective_user
        mem  = sc.memory(user.id)
        mem.remember("name", user.first_name)
        if user.username:
            mem.remember("username", f"@{user.username}")

        agents_list = "\n".join(f"  • `{a}`" for a in agents)
        await update.message.reply_text(
            f"👋 Hello *{user.first_name}*\\!\n\n"
            f"I'm powered by *SimpleContext* — an AI brain with memory\\.\n\n"
            f"🤖 *Available agents:*\n{agents_list}\n\n"
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
            "/memory — Show your saved profile\n",
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
                f"Use `/agent <name>` or `/agent auto`",
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
        await update.message.reply_text(
            f"📊 *Status*\n\n"
            f"🤖 Agent: `{result.agent_id}`\n"
            f"💬 Messages: `{mem.count()}`\n"
            f"🧠 Agents loaded: `{len(agents)}`",
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

    async def handle_message(update: Update, ctx):
        uid  = update.effective_user.id
        user = update.effective_user
        text = update.message.text

        # Auto-save name
        mem = sc.memory(uid)
        if not mem.recall("name"):
            mem.remember("name", user.first_name)
            if user.username:
                mem.remember("username", f"@{user.username}")

        await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

        # Route + prepare messages
        result   = sc.router.route(uid, text)
        messages = sc.prepare_messages(uid, text, result)

        logger.info(f"[{user.username or uid}] → agent={result.agent_id}")

        # Call LLM
        reply = llm.call(messages, max_tokens=1024)

        # Chain check
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

        # Send to Telegram
        try:
            await update.message.reply_text(reply, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(reply)

    # ── Build App ──────────────────────────────────────────

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("agents",  cmd_agents))
    app.add_handler(CommandHandler("agent",   cmd_agent))
    app.add_handler(CommandHandler("clear",   cmd_clear))
    app.add_handler(CommandHandler("status",  cmd_status))
    app.add_handler(CommandHandler("memory",  cmd_memory))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot is running... (Ctrl+C to stop)")
    app.run_polling(drop_pending_updates=True)
