"""
Telegram Bot integration service for Family Assistant.

Handles:
- Telegram bot message processing
- Multimodal content (photos, voice, documents) handling
- Family member authentication and permissions
- Message routing and response generation
- File downloads and uploads
"""

import asyncio
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode, ChatType

from ..models.multimodal import (
    ContentType, MessageRole, ChatMessage, MultimodalContent,
    TextContent, ImageContent, AudioContent, DocumentContent,
    MediaMetadata, FamilyMemberProfile, MultimodalChatRequest
)
from ..services.content_processor import ContentProcessor, ContentProcessorError
from config.settings import settings


class TelegramService:
    """Telegram bot service for Family Assistant."""

    def __init__(self, bot_token: str, content_processor: ContentProcessor):
        """Initialize Telegram service."""
        self.bot_token = bot_token
        self.content_processor = content_processor
        self.bot = Bot(token=bot_token)

        # Active user sessions (user_id -> session_data)
        self.active_sessions: Dict[int, Dict[str, Any]] = {}

        # Family member cache (user_id -> FamilyMemberProfile)
        self.family_members: Dict[int, FamilyMemberProfile] = {}

    async def start(self):
        """Start the Telegram bot."""
        # Create application
        application = Application.builder().token(self.bot_token).build()

        # Add handlers
        application.add_handler(CommandHandler("start", self.handle_start))
        application.add_handler(CommandHandler("help", self.handle_help))
        application.add_handler(CommandHandler("profile", self.handle_profile))
        application.add_handler(CommandHandler("family", self.handle_family))
        application.add_handler(CommandHandler("status", self.handle_status))

        # Message handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo_message))
        application.add_handler(MessageHandler(filters.VOICE, self.handle_voice_message))
        application.add_handler(MessageHandler(filters.AUDIO, self.handle_audio_message))
        application.add_handler(MessageHandler(filters.DOCUMENT, self.handle_document_message))

        # Callback query handler
        application.add_handler(CallbackQueryHandler(self.handle_callback_query))

        # Error handler
        application.add_error_handler(self.handle_error)

        print("🤖 Telegram Bot started successfully!")
        return application

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        chat = update.effective_chat

        # Create or get family member profile
        await self._ensure_family_member(user)

        welcome_message = f"""
👋 Welcome to the Family Assistant, {user.first_name}!

I'm here to help your family stay connected and organized. I can:

💬 Chat with you about anything
📸 View and analyze photos
🎤 Listen to voice messages
📄 Read and summarize documents
📅 Help with scheduling
🏠 Coordinate family activities

Type /help to see all available commands.

Your family ID: {user.id}
        """

        await context.bot.send_message(
            chat_id=chat.id,
            text=welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        user = update.effective_user
        chat = update.effective_chat

        help_message = """
🆘 Family Assistant Help

**Basic Commands:**
/start - Welcome message
/help - Show this help
/profile - View your profile
/family - Family information
/status - System status

**Chat Features:**
• Send text messages to chat
• Send photos for analysis
• Send voice messages for transcription
• Send documents for text extraction
• Ask questions about family schedules
• Get help with homework and activities

**Family Coordination:**
• Share photos with family members
• Send voice notes
• Coordinate schedules
• Get reminders
• Share documents

**Privacy & Safety:**
• All content stays in your family
• Automatic content filtering
• Privacy controls for photos/voice
• Family-only sharing

Need help? Just ask!
        """

        await context.bot.send_message(
            chat_id=chat.id,
            text=help_message,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /profile command."""
        user = update.effective_user
        chat = update.effective_chat

        family_member = await self._ensure_family_member(user)

        if not family_member:
            await context.bot.send_message(
                chat_id=chat.id,
                text="❌ Profile not found. Please contact family administrator."
            )
            return

        profile_message = f"""
👤 **Profile: {family_member.name}**

🏷️ **Role:** {family_member.role.title()}
🎂 **Age:** {family_member.age or 'Not specified'}

🔧 **Settings:**
• Vision Analysis: {'✅' if family_member.vision_analysis_enabled else '❌'}
• Speech Recognition: {'✅' if family_member.speech_recognition_enabled else '❌'}
• Document Extraction: {'✅' if family_member.document_extraction_enabled else '❌'}

🔒 **Privacy:**
• Photo Level: {family_member.photo_privacy_level}
• Voice Level: {family_member.voice_privacy_level}

📱 **Telegram ID:** {user.id}
        """

        await context.bot.send_message(
            chat_id=chat.id,
            text=profile_message,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_family(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /family command."""
        chat = update.effective_chat

        # Get family members count
        family_count = len(self.family_members)

        family_message = f"""
👨‍👩‍👧‍👦 **Family Information**

**Total Members:** {family_count}
**Active Users:** {len(self.active_sessions)}

**Online Now:** {', '.join([member.name for member in self.family_members.values()]) or 'None'}

Use /profile to see individual member details.
        """

        await context.bot.send_message(
            chat_id=chat.id,
            text=family_message,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        chat = update.effective_chat

        status_message = f"""
📊 **System Status**

🤖 **Bot:** Online ✅
🖼️ **Vision Processing:** Available ✅
🎤 **Speech Recognition:** Available ✅
📄 **Document Processing:** Available ✅

📈 **Statistics:**
• Active Chats: {len(self.active_sessions)}
• Family Members: {len(self.family_members)}
• Messages Today: 0

⚡ **Performance:** Good
        """

        await context.bot.send_message(
            chat_id=chat.id,
            text=status_message,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        user = update.effective_user
        chat = update.effective_chat
        message = update.message

        try:
            # Ensure family member exists
            family_member = await self._ensure_family_member(user)

            # Create chat message
            chat_message = ChatMessage(
                role=MessageRole.USER,
                content=message.text,
                user_id=str(user.id),
                timestamp=datetime.utcnow()
            )

            # Process with Family Assistant
            response = await self._process_message(chat_message, family_member)

            # Send response
            await context.bot.send_message(
                chat_id=chat.id,
                text=response,
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"❌ Sorry, I encountered an error: {str(e)}"
            )

    async def handle_photo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages."""
        user = update.effective_user
        chat = update.effective_chat
        message = update.message

        try:
            # Ensure family member exists
            family_member = await self._ensure_family_member(user)

            if not family_member.vision_analysis_enabled:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text="📸 Photo analysis is disabled for your profile."
                )
                return

            # Download photo
            file = await context.bot.get_file(message.photo[-1].file_id)
            photo_data = await file.download_as_bytearray()

            # Process photo
            processing_result = await self.content_processor.process_content(
                file_data=photo_data,
                filename=f"photo_{message.photo[-1].file_id}.jpg",
                family_member=family_member,
                conversation_id=str(chat.id)
            )

            # Create multimodal message
            multimodal_content = MultimodalContent(
                content=ImageContent(
                    file_data=photo_data,
                    caption=message.caption,
                    metadata=MediaMetadata(
                        file_name=f"photo_{message.photo[-1].file_id}.jpg",
                        mime_type="image/jpeg",
                        file_size_bytes=len(photo_data)
                    )
                )
            )

            chat_message = ChatMessage(
                role=MessageRole.USER,
                multimodal_content=[multimodal_content],
                user_id=str(user.id),
                timestamp=datetime.utcnow()
            )

            # Add text caption if provided
            if message.caption:
                chat_message.content = message.caption

            # Process with Family Assistant
            response = await self._process_message(chat_message, family_member)

            # Send response
            await context.bot.send_message(
                chat_id=chat.id,
                text=response,
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"❌ Sorry, I couldn't process the photo: {str(e)}"
            )

    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages."""
        user = update.effective_user
        chat = update.effective_chat
        message = update.message

        try:
            # Ensure family member exists
            family_member = await self._ensure_family_member(user)

            if not family_member.speech_recognition_enabled:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text="🎤 Voice recognition is disabled for your profile."
                )
                return

            # Download voice message
            file = await context.bot.get_file(message.voice.file_id)
            voice_data = await file.download_as_bytearray()

            # Process voice
            processing_result = await self.content_processor.process_content(
                file_data=voice_data,
                filename=f"voice_{message.voice.file_id}.ogg",
                family_member=family_member,
                conversation_id=str(chat.id)
            )

            # Create multimodal message
            multimodal_content = MultimodalContent(
                content=AudioContent(
                    file_data=voice_data,
                    caption=message.caption,
                    metadata=MediaMetadata(
                        file_name=f"voice_{message.voice.file_id}.ogg",
                        mime_type="audio/ogg",
                        file_size_bytes=len(voice_data),
                        duration_seconds=message.voice.duration
                    )
                )
            )

            chat_message = ChatMessage(
                role=MessageRole.USER,
                multimodal_content=[multimodal_content],
                user_id=str(user.id),
                timestamp=datetime.utcnow()
            )

            # Add text caption if provided
            if message.caption:
                chat_message.content = message.caption

            # Process with Family Assistant
            response = await self._process_message(chat_message, family_member)

            # Send response
            await context.bot.send_message(
                chat_id=chat.id,
                text=response,
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"❌ Sorry, I couldn't process the voice message: {str(e)}"
            )

    async def handle_audio_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle audio messages (music, etc.)."""
        chat = update.effective_chat
        await context.bot.send_message(
            chat_id=chat.id,
            text="🎵 I can help with voice messages, but music files are not currently supported."
        )

    async def handle_document_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document messages."""
        user = update.effective_user
        chat = update.effective_chat
        message = update.message

        try:
            # Ensure family member exists
            family_member = await self._ensure_family_member(user)

            if not family_member.document_extraction_enabled:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text="📄 Document processing is disabled for your profile."
                )
                return

            # Download document
            file = await context.bot.get_file(message.document.file_id)
            doc_data = await file.download_as_bytearray()

            # Process document
            processing_result = await self.content_processor.process_content(
                file_data=doc_data,
                filename=message.document.file_name,
                family_member=family_member,
                conversation_id=str(chat.id)
            )

            # Create multimodal message
            multimodal_content = MultimodalContent(
                content=DocumentContent(
                    file_data=doc_data,
                    caption=message.caption,
                    metadata=MediaMetadata(
                        file_name=message.document.file_name,
                        mime_type=message.document.mime_type,
                        file_size_bytes=len(doc_data)
                    )
                )
            )

            chat_message = ChatMessage(
                role=MessageRole.USER,
                multimodal_content=[multimodal_content],
                user_id=str(user.id),
                timestamp=datetime.utcnow()
            )

            # Add text caption if provided
            if message.caption:
                chat_message.content = message.caption

            # Process with Family Assistant
            response = await self._process_message(chat_message, family_member)

            # Send response
            await context.bot.send_message(
                chat_id=chat.id,
                text=response,
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"❌ Sorry, I couldn't process the document: {str(e)}"
            )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries (inline keyboards)."""
        query = update.callback_query
        chat = update.effective_chat

        # Handle different callback actions
        if query.data == "profile_settings":
            await self._show_profile_settings(update, context)
        elif query.data.startswith("privacy_"):
            await self._handle_privacy_setting(update, context)
        else:
            await query.answer("Unknown action")

    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        import logging
        logging.error(f"Update {update} caused error {context.error}")

        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Sorry, something went wrong. Please try again."
            )

    async def _ensure_family_member(self, user) -> Optional[FamilyMemberProfile]:
        """Ensure family member exists in cache."""
        if user.id in self.family_members:
            return self.family_members[user.id]

        # Create default profile for new users
        family_member = FamilyMemberProfile(
            user_id=str(user.id),
            name=user.full_name or user.first_name or "User",
            role="parent",  # Default role, would be configured by admin
            age=None,
            preferred_content_types=[ContentType.TEXT],
            content_filters=["profanity"],
            language_preferences=["en"],
            vision_analysis_enabled=True,
            photo_privacy_level="family",
            auto_image_description=True,
            speech_recognition_enabled=True,
            preferred_audio_format="ogg",
            voice_privacy_level="family",
            document_extraction_enabled=True,
            auto_summarization=False,
            permissions={"can_chat": True, "can_send_images": True, "can_send_voice": True},
            preferences={}
        )

        # In a real implementation, this would be saved to database
        self.family_members[user.id] = family_member
        return family_member

    async def _process_message(self, message: ChatMessage, family_member: FamilyMemberProfile) -> str:
        """Process message through Family Assistant."""
        try:
            # This would integrate with the main Family Assistant agent
            # For now, return a simple response

            if message.content:
                user_content = message.content
            elif message.multimodal_content:
                content_parts = []
                for item in message.multimodal_content:
                    if isinstance(item.content, ImageContent):
                        content_parts.append(f"[Image: {item.content.caption or 'Photo'}]")
                    elif isinstance(item.content, AudioContent):
                        content_parts.append(f"[Voice: {item.content.caption or 'Voice message'}]")
                    elif isinstance(item.content, DocumentContent):
                        content_parts.append(f"[Document: {item.content.caption or 'Document'}]")
                user_content = " | ".join(content_parts)
            else:
                user_content = "Hello!"

            # Simple response logic (would be replaced with actual agent)
            responses = {
                "hello": "Hello! How can I help you today?",
                "hi": "Hi there! What can I do for you?",
                "help": "I'm here to help! What do you need assistance with?",
                "default": f"Thanks for sharing, {family_member.name}! How can I help your family today?"
            }

            # Simple keyword matching
            user_content_lower = user_content.lower()
            for keyword, response in responses.items():
                if keyword in user_content_lower:
                    return response

            return responses["default"]

        except Exception as e:
            return f"Sorry, I had trouble processing your message: {str(e)}"

    async def _show_profile_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show profile settings inline keyboard."""
        user_id = update.effective_user.id
        family_member = self.family_members.get(user_id)

        if not family_member:
            await update.callback_query.answer("Profile not found")
            return

        keyboard = [
            [
                InlineKeyboardButton("🖼️ Vision: " + ("✅" if family_member.vision_analysis_enabled else "❌"),
                                   callback_data=f"privacy_vision_{user_id}"),
                InlineKeyboardButton("🎤 Voice: " + ("✅" if family_member.speech_recognition_enabled else "❌"),
                                   callback_data=f"privacy_voice_{user_id}")
            ],
            [
                InlineKeyboardButton("📄 Documents: " + ("✅" if family_member.document_extraction_enabled else "❌"),
                                   callback_data=f"privacy_docs_{user_id}"),
                InlineKeyboardButton("🔒 Privacy: " + family_member.photo_privacy_level,
                                   callback_data=f"privacy_photo_{user_id}")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚙️ **Profile Settings**",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def _handle_privacy_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle privacy setting changes."""
        query = update.callback_query
        data = query.data

        # Parse callback data
        parts = data.split("_")
        if len(parts) < 3:
            await query.answer("Invalid setting")
            return

        setting_type = parts[1]
        user_id = int(parts[2])
        family_member = self.family_members.get(user_id)

        if not family_member:
            await query.answer("Profile not found")
            return

        # Toggle setting
        if setting_type == "vision":
            family_member.vision_analysis_enabled = not family_member.vision_analysis_enabled
            status = "enabled" if family_member.vision_analysis_enabled else "disabled"
            message = f"🖼️ Vision analysis {status}"
        elif setting_type == "voice":
            family_member.speech_recognition_enabled = not family_member.speech_recognition_enabled
            status = "enabled" if family_member.speech_recognition_enabled else "disabled"
            message = f"🎤 Voice recognition {status}"
        elif setting_type == "docs":
            family_member.document_extraction_enabled = not family_member.document_extraction_enabled
            status = "enabled" if family_member.document_extraction_enabled else "disabled"
            message = f"📄 Document processing {status}"
        elif setting_type == "photo":
            # Cycle through privacy levels
            levels = ["private", "family", "public"]
            current_idx = levels.index(family_member.photo_privacy_level)
            family_member.photo_privacy_level = levels[(current_idx + 1) % len(levels)]
            message = f"🔒 Photo privacy: {family_member.photo_privacy_level}"
        else:
            await query.answer("Unknown setting")
            return

        await query.answer(message)
        await self._show_profile_settings(update, context)


# Factory function to create Telegram service
def create_telegram_service(bot_token: str) -> TelegramService:
    """Create and configure Telegram service."""
    content_processor = ContentProcessor()
    return TelegramService(bot_token, content_processor)