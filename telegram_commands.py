"""
OpenClaw Telegram Memory Commands
Add to your Telegram bot handler
"""

import sys
sys.path.insert(0, '/root/.openclaw/extensions/memory-manager')

from memory_manager import get_memory

# Global memory instance
_memory = None

def get_memory_instance():
    """Lazy load memory"""
    global _memory
    if _memory is None:
        _memory = get_memory()
    return _memory


# =================================================================
# COMMAND HANDLERS
# =================================================================

async def cmd_remember(update, context):
    """
    /remember [text]
    Store something in memory
    
    Examples:
      /remember My API key is abc123
      /remember I prefer dark mode
    """
    memory = get_memory_instance()
    
    # Get text after command
    text = ' '.join(context.args)
    
    if not text:
        await update.message.reply_text(
            "❌ Please provide text to remember\n"
            "Usage: /remember [text]"
        )
        return
    
    # Store with Telegram context
    user = update.effective_user.username or update.effective_user.first_name
    chat_id = update.effective_chat.id
    
    memory_id = memory.remember(
        content=text,
        source='telegram',
        metadata={
            'user': user,
            'chat_id': chat_id,
            'message_id': update.message.message_id
        }
    )
    
    await update.message.reply_text(
        f"✅ Remembered!\n"
        f"ID: `{memory_id}`",
        parse_mode='Markdown'
    )


async def cmd_recall(update, context):
    """
    /recall [query]
    Search memories
    
    Examples:
      /recall API key
      /recall what did I say about dark mode
    """
    memory = get_memory_instance()
    
    query = ' '.join(context.args)
    
    if not query:
        await update.message.reply_text(
            "❌ Please provide a search query\n"
            "Usage: /recall [query]"
        )
        return
    
    # Search
    results = memory.recall(query, n_results=5)
    
    if not results:
        await update.message.reply_text("🔍 No memories found")
        return
    
    # Format results
    response = f"🔍 Found {len(results)} memories:\n\n"
    
    for i, r in enumerate(results, 1):
        content = r['content'][:200]
        if len(r['content']) > 200:
            content += "..."
        
        source_emoji = {
            'telegram': '💬',
            'session': '🤖',
            'migrated': '📁',
            'file': '📄'
        }.get(r['source'], '📝')
        
        response += f"{i}. {source_emoji} {content}\n"
        response += f"   _Source: {r['source']} | {r['timestamp'][:10]}_\n\n"
    
    await update.message.reply_text(response, parse_mode='Markdown')


async def cmd_forget(update, context):
    """
    /forget [memory_id]
    Delete a memory by ID
    
    Example:
      /forget abc123
    """
    memory = get_memory_instance()
    
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide memory ID\n"
            "Usage: /forget [memory_id]"
        )
        return
    
    memory_id = context.args[0]
    
    if memory.forget(memory_id):
        await update.message.reply_text(f"🗑️ Forgot: `{memory_id}`", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ Memory not found: `{memory_id}`", parse_mode='Markdown')


async def cmd_memory_stats(update, context):
    """
    /memory_stats
    Show memory statistics
    """
    memory = get_memory_instance()
    stats = memory.stats()
    
    response = "📊 *Memory Statistics*\n\n"
    response += f"Backend: `{stats.get('backend', 'unknown')}`\n"
    response += f"Status: {stats.get('status', 'unknown')}\n"
    
    if 'total_documents' in stats:
        response += f"Total memories: `{stats['total_documents']}`\n"
    
    await update.message.reply_text(response, parse_mode='Markdown')


async def cmd_what_do_i_know(update, context):
    """
    /what_do_i_know [about topic]
    Show what I know about a topic
    
    Examples:
      /what_do_i_know about you
      /what_do_i_know OpenClaw
    """
    memory = get_memory_instance()
    
    topic = ' '.join(context.args) or "you"
    
    # Search for topic
    results = memory.recall(f"what do I know about {topic}", n_results=10)
    
    if not results:
        await update.message.reply_text(f"🤔 I don't know much about {topic} yet")
        return
    
    # Group by source
    by_source = {}
    for r in results:
        source = r['source']
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(r)
    
    response = f"🧠 *What I know about {topic}:*\n\n"
    
    for source, items in by_source.items():
        source_name = {
            'telegram': '💬 From our chats',
            'session': '🤖 From sessions',
            'migrated': '📁 From files'
        }.get(source, f'📝 From {source}')
        
        response += f"*{source_name}:*\n"
        for item in items[:3]:  # Max 3 per source
            content = item['content'][:100].replace('\n', ' ')
            if len(item['content']) > 100:
                content += "..."
            response += f"• {content}\n"
        response += "\n"
    
    await update.message.reply_text(response, parse_mode='Markdown')


# =================================================================
# AUTO-REMEMBER MESSAGES
# =================================================================

async def auto_remember_message(update, context):
    """
    Automatically remember important messages
    Call this from your message handler
    """
    memory = get_memory_instance()
    
    message = update.message
    if not message or not message.text:
        return
    
    text = message.text
    user = message.from_user.username or message.from_user.first_name
    
    # Skip commands
    if text.startswith('/'):
        return
    
    # Skip short messages
    if len(text) < 20:
        return
    
    # Check if message seems important
    important_keywords = [
        'remember', 'important', 'note', 'api', 'key', 'password',
        'prefer', 'like', 'want', 'need', 'should', 'always',
        'my name', 'I am', 'I work', 'I live'
    ]
    
    is_important = any(kw in text.lower() for kw in important_keywords)
    
    if is_important:
        # Store silently (no reply)
        memory.remember_telegram_message(
            message=message.to_dict(),
            context=f"Auto-captured from {user}"
        )
        
        # Optional: React with emoji to show it was remembered
        # await message.react('🧠')


# =================================================================
# SETUP FUNCTION
# =================================================================

def setup_memory_handlers(application):
    """
    Add memory handlers to Telegram application
    
    Usage:
        from telegram_memory_commands import setup_memory_handlers
        setup_memory_handlers(application)
    """
    from telegram.ext import CommandHandler, MessageHandler, filters
    
    # Command handlers
    application.add_handler(CommandHandler("remember", cmd_remember))
    application.add_handler(CommandHandler("recall", cmd_recall))
    application.add_handler(CommandHandler("forget", cmd_forget))
    application.add_handler(CommandHandler("memory_stats", cmd_memory_stats))
    application.add_handler(CommandHandler("what_do_i_know", cmd_what_do_i_know))
    
    # Auto-remember important messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, auto_remember_message),
        group=1  # Run after other handlers
    )
    
    print("[Telegram] Memory commands registered:")
    print("  /remember [text] - Store memory")
    print("  /recall [query] - Search memories")
    print("  /forget [id] - Delete memory")
    print("  /memory_stats - Show stats")
    print("  /what_do_i_know [topic] - Show knowledge")
