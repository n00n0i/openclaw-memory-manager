#!/usr/bin/env python3
"""
OpenClaw Telegram Bot with Memory
Complete integration example
"""

import os
import sys
import asyncio

# Add memory manager to path
sys.path.insert(0, '/root/.openclaw/extensions/memory-manager')

from memory_manager import get_memory

# Telegram imports
try:
    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        ContextTypes,
        filters
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("[Bot] python-telegram-bot not installed")
    print("[Bot] Run: pip install python-telegram-bot")


class OpenClawTelegramBot:
    """Telegram bot with integrated memory"""
    
    def __init__(self, token: str = None):
        self.token = token or os.environ.get('TELEGRAM_BOT_TOKEN')
        self.memory = get_memory()
        self.application = None
        
        if not self.token:
            raise ValueError("Telegram bot token required")
    
    async def start(self):
        """Start the bot"""
        if not TELEGRAM_AVAILABLE:
            print("[Bot] Cannot start - telegram library not available")
            return
        
        # Create application
        self.application = Application.builder().token(self.token).build()
        
        # Add handlers
        self._setup_handlers()
        
        # Start
        print("[Bot] Starting OpenClaw Telegram Bot with Memory...")
        print(f"[Bot] Memory backend: {self.memory.backend_type}")
        print(f"[Bot] Memories: {self.memory.stats().get('total_documents', 0)}")
        
        await self.application.initialize()
        await self.application.start()
        await self.application.run_polling()
    
    def _setup_handlers(self):
        """Setup command and message handlers"""
        
        # Basic commands
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        
        # Memory commands
        self.application.add_handler(CommandHandler("remember", self.cmd_remember))
        self.application.add_handler(CommandHandler("recall", self.cmd_recall))
        self.application.add_handler(CommandHandler("forget", self.cmd_forget))
        self.application.add_handler(CommandHandler("memory", self.cmd_memory_stats))
        self.application.add_handler(CommandHandler("know", self.cmd_what_do_i_know))
        
        # Auto-remember messages
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message),
            group=1
        )
    
    # =================================================================
    # COMMAND HANDLERS
    # =================================================================
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command"""
        user = update.effective_user.first_name
        
        welcome = f"""
👋 Hello {user}! I'm OpenClaw with Memory.

I can remember our conversations and recall them later.

*Memory Commands:*
/remember [text] - Store something important
/recall [query] - Search my memories
/forget [id] - Delete a memory
/memory - Show memory stats
/know [topic] - What I know about something

Try: /remember I prefer dark mode
Then: /recall dark mode
        """.strip()
        
        await update.message.reply_text(welcome, parse_mode='Markdown')
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command"""
        help_text = """
*OpenClaw Memory Bot Help*

*Store Memories:*
/remember [text]
Example: `/remember My API key is xyz123`

*Search Memories:*
/recall [query]
Example: `/recall API key`

*Delete Memory:*
/forget [memory_id]
Example: `/forget abc123def`

*View Stats:*
/memory
Shows memory statistics

*Query Knowledge:*
/know [topic]
Example: `/know about you`

*Tips:*
• I automatically remember important messages
• Use natural language in searches
• Memories are private to this chat
        """.strip()
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def cmd_remember(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remember command"""
        text = ' '.join(context.args)
        
        if not text:
            await update.message.reply_text(
                "❌ Please provide text to remember\n"
                "Usage: `/remember [text]`",
                parse_mode='Markdown'
            )
            return
        
        user = update.effective_user.username or update.effective_user.first_name
        
        memory_id = self.memory.remember(
            content=text,
            source='telegram',
            metadata={
                'user': user,
                'chat_id': update.effective_chat.id,
                'chat_type': update.effective_chat.type
            }
        )
        
        await update.message.reply_text(
            f"✅ *Remembered!*\n"
            f"`{memory_id}`",
            parse_mode='Markdown'
        )
    
    async def cmd_recall(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recall command"""
        query = ' '.join(context.args)
        
        if not query:
            await update.message.reply_text(
                "❌ Please provide a search query\n"
                "Usage: `/recall [query]`",
                parse_mode='Markdown'
            )
            return
        
        results = self.memory.recall(query, n_results=5)
        
        if not results:
            await update.message.reply_text("🔍 *No memories found*", parse_mode='Markdown')
            return
        
        response = f"🔍 *Found {len(results)} memories:*\n\n"
        
        for i, r in enumerate(results, 1):
            content = r['content'][:150]
            if len(r['content']) > 150:
                content += "..."
            
            # Escape markdown
            content = content.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
            
            response += f"*{i}.* {content}\n"
            response += f"   _{r['source']} | {r['timestamp'][:10]}_\n\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def cmd_forget(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Forget command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide memory ID\n"
                "Usage: `/forget [memory_id]`",
                parse_mode='Markdown'
            )
            return
        
        memory_id = context.args[0]
        
        if self.memory.forget(memory_id):
            await update.message.reply_text(f"🗑️ *Forgotten:* `{memory_id}`", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ *Memory not found:* `{memory_id}`", parse_mode='Markdown')
    
    async def cmd_memory_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Memory stats command"""
        stats = self.memory.stats()
        
        response = "📊 *Memory Statistics*\n\n"
        response += f"Backend: `{stats.get('backend', 'unknown')}`\n"
        response += f"Status: {stats.get('status', 'unknown')}\n"
        
        if 'total_documents' in stats:
            response += f"Total memories: `{stats['total_documents']}`\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def cmd_what_do_i_know(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """What do I know command"""
        topic = ' '.join(context.args) or "you"
        
        results = self.memory.recall(f"what do I know about {topic}", n_results=8)
        
        if not results:
            await update.message.reply_text(
                f"🤔 *I don't know much about {topic} yet*\n"
                f"Tell me something! Use `/remember [text]`",
                parse_mode='Markdown'
            )
            return
        
        response = f"🧠 *What I know about {topic}:*\n\n"
        
        for i, r in enumerate(results[:5], 1):
            content = r['content'][:120]
            if len(r['content']) > 120:
                content += "..."
            
            # Escape markdown
            content = content.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
            
            response += f"*{i}.* {content}\n"
            response += f"   _{r['timestamp'][:10]}_\n\n"
        
        if len(results) > 5:
            response += f"_...and {len(results) - 5} more_"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    # =================================================================
    # MESSAGE HANDLER
    # =================================================================
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages - auto-remember important ones"""
        message = update.message
        if not message or not message.text:
            return
        
        text = message.text
        
        # Skip short messages
        if len(text) < 30:
            return
        
        # Check for importance indicators
        important_patterns = [
            r'\b(remember|note|important)\b',
            r'\b(my\s+(name|email|phone|address))',
            r'\b(I\s+(prefer|like|want|need|hate))',
            r'\b(API\s+key|password|token|secret)\b',
            r'\b(always|never|usually)\b',
        ]
        
        import re
        is_important = any(re.search(p, text, re.IGNORECASE) for p in important_patterns)
        
        if is_important:
            # Remember silently
            self.memory.remember_telegram_message(
                message=message.to_dict(),
                context="Auto-captured important message"
            )
            
            # Optional: React with emoji
            try:
                await message.set_reaction('🧠')
            except:
                pass  # Reaction might not be available


# =================================================================
# MAIN
# =================================================================

def main():
    """Run the bot"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', help='Telegram bot token')
    args = parser.parse_args()
    
    # Get token
    token = args.token or os.environ.get('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("Error: Telegram bot token required")
        print("Set TELEGRAM_BOT_TOKEN environment variable or use --token")
        sys.exit(1)
    
    # Create and run bot
    bot = OpenClawTelegramBot(token)
    
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        print("\n[Bot] Stopping...")


if __name__ == "__main__":
    main()
