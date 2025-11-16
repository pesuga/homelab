"""
Family Context Engine

Core engine for processing family interactions with role-based personalization,
bilingual support, and memory integration.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

try:
    from .llm_service import LLMService, LLMMessage, LLMResponse
    from .family_context import FamilyContextService
    from .memory_service import MemoryService
    from ..models.database import Family, FamilyMember, FamilyInteraction, FamilyMemory
except ImportError:
    from services.llm_service import LLMService, LLMMessage, LLMResponse
    from services.family_context import FamilyContextService
    from services.memory_service import MemoryService
    from models.database import Family, FamilyMember, FamilyInteraction, FamilyMemory

logger = logging.getLogger(__name__)

class FamilyContext(BaseModel):
    """Family context for interaction processing."""
    family_id: str
    family_name: str
    family_code: str
    primary_language: str = "es"
    secondary_language: str = "en"
    member_id: str
    member_name: str
    member_role: str  # parent, teenager, child, grandparent
    member_preferences: Dict[str, Any] = {}
    parental_controls: Dict[str, Any] = {}

class InteractionRequest(BaseModel):
    """Request for family interaction processing."""
    message: str
    interaction_type: str = "text"  # text, voice, command
    language: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    member_id: str

class InteractionResponse(BaseModel):
    """Response from family interaction processing."""
    response: str
    interaction_id: str
    timestamp: datetime
    language: str
    sentiment: str = "neutral"
    memories_accessed: List[str] = []
    follow_up_suggestions: List[str] = []
    processing_time: float

class FamilyEngine:
    """Core engine for family AI interactions."""

    def __init__(
        self,
        llm_service: LLMService,
        family_context_service: FamilyContextService,
        memory_service: MemoryService,
        db: Session
    ):
        self.llm_service = llm_service
        self.family_context_service = family_context_service
        self.memory_service = memory_service
        self.db = db

    async def get_family_context(self, family_id: str, member_id: str) -> Optional[FamilyContext]:
        """Get family context for interaction."""
        try:
            # Get family information
            family = self.db.query(Family).filter(Family.id == family_id).first()
            if not family:
                return None

            # Get member information
            member = self.db.query(FamilyMember).filter(
                FamilyMember.id == member_id,
                FamilyMember.family_id == family_id
            ).first()
            if not member:
                return None

            # Get family settings
            family_settings = self.family_context_service.get_family_settings(family_id)

            # Build context
            return FamilyContext(
                family_id=family.id,
                family_name=family.name,
                family_code=family.family_code,
                primary_language=family.primary_language,
                secondary_language=family.secondary_language,
                member_id=member.id,
                member_name=member.name,
                member_role=member.role,
                member_preferences=member.preferences or {},
                parental_controls=family_settings.get("parental_controls", {})
            )

        except Exception as e:
            logger.error(f"Failed to get family context: {e}")
            return None

    def detect_language(self, text: str) -> str:
        """Simple language detection based on common words."""
        spanish_indicators = [
            "hola", "gracias", "por favor", "¿qué", "cómo", "dónde", "cuándo", "por qué",
            "el", "la", "los", "las", "un", "una", "gustar", "querer", "poder", "tener"
        ]

        text_lower = text.lower()
        spanish_words = sum(1 for word in spanish_indicators if word in text_lower)

        # Simple heuristic: if more than 2 Spanish indicators, assume Spanish
        return "es" if spanish_words > 2 else "en"

    def apply_parental_controls(
        self,
        context: FamilyContext,
        message: str,
        response: str
    ) -> Tuple[str, str]:
        """Apply parental controls and content filtering."""
        if context.member_role in ["parent", "grandparent"]:
            # Parents and grandparents get full access
            return message, response

        # Get parental control settings
        controls = context.parental_controls

        # Content filtering for children
        if context.member_role == "child" and controls.get("content_filter", True):
            # Simple content filtering - in production, use more sophisticated filtering
            blocked_topics = controls.get("blocked_topics", [])

            # Check for blocked topics in both message and response
            for topic in blocked_topics:
                if topic.lower() in message.lower() or topic.lower() in response.lower():
                    response = "Lo siento, no puedo ayudar con ese tema. Puedes preguntarle a tus padres sobre esto."
                    break

        # Screen time checks for children/teenagers
        if context.member_role in ["child", "teenager"]:
            current_hour = datetime.now().hour
            bedtime = controls.get("bedtime_hour", 21)
            wakeup = controls.get("wakeup_hour", 7)

            if current_hour >= bedtime or current_hour <= wakeup:
                if "que hora es" in message.lower() or "what time" in message.lower():
                    response = f"Son las {current_hour}:{datetime.now().minute:02d}. Es hora de descansar. ¡Hasta mañana!"
                else:
                    response = "Es hora de descansar. Podemos continuar conversando mañana."

        return message, response

    def detect_sentiment(self, text: str) -> str:
        """Simple sentiment detection."""
        positive_words = ["gracias", "feliz", "bueno", "excelente", "perfecto", "genial", "thank", "happy", "good", "great"]
        negative_words = ["enojado", "triste", "malo", "problema", "error", "angry", "sad", "bad", "problem"]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def generate_follow_up_suggestions(
        self,
        context: FamilyContext,
        message: str,
        response: str
    ) -> List[str]:
        """Generate follow-up suggestions based on context."""
        suggestions = []

        # Question-based suggestions
        if "?" not in message:
            suggestions.append("¿Necesitas ayuda con algo específico?")

        # Role-specific suggestions
        if context.member_role == "parent":
            suggestions.extend([
                "¿Quieres ayuda con la organización familiar?",
                "Puedo sugerir actividades educativas para los niños"
            ])
        elif context.member_role == "teenager":
            suggestions.extend([
                "¿Necesitas ayuda con tus estudios?",
                "¿Quieres consejos para organizar tu tiempo?"
            ])
        elif context.member_role == "child":
            suggestions.extend([
                "¿Quieres aprender algo nuevo?",
                "¿Necesitas ayuda con tu tarea?"
            ])

        return suggestions[:3]  # Limit to 3 suggestions

    async def process_interaction(self, request: InteractionRequest) -> InteractionResponse:
        """Process a family interaction request."""
        import time
        start_time = time.time()

        try:
            # Generate interaction ID
            interaction_id = str(uuid.uuid4())
            timestamp = datetime.now()

            # Get family context
            context = await self.get_family_context(request.context.get("family_id"), request.member_id)
            if not context:
                raise Exception("Family context not found")

            # Detect language if not specified
            language = request.language or self.detect_language(request.message)

            # Retrieve relevant memories
            relevant_memories = await self.memory_service.search_memories(
                context.family_id,
                request.message,
                limit=5
            )

            # Build conversation context with memories
            memory_context = ""
            if relevant_memories:
                memory_context = "\\n\\n🧠 **MEMORIAS RELEVANTES**:\\n"
                for memory in relevant_memories:
                    memory_context += f"- {memory.get('title', 'Sin título')}: {memory.get('content', '')[:100]}...\\n"

            # Prepare LLM messages
            messages = [
                LLMMessage(
                    role="system",
                    content="",  # System prompt will be added by LLM service
                    family_context=context.dict()
                ),
                LLMMessage(
                    role="user",
                    content=request.message + memory_context
                )
            ]

            # Generate response using LLM
            llm_response = await self.llm_service.generate(
                messages=messages,
                family_context=context.dict()
            )

            # Apply parental controls
            filtered_message, filtered_response = self.apply_parental_controls(
                context,
                request.message,
                llm_response.content
            )

            # Detect sentiment
            sentiment = self.detect_sentiment(request.message)

            # Generate follow-up suggestions
            follow_up_suggestions = self.generate_follow_up_suggestions(
                context,
                request.message,
                filtered_response
            )

            # Log interaction
            interaction = FamilyInteraction(
                id=interaction_id,
                family_id=context.family_id,
                family_member_id=context.member_id,
                interaction_type=request.interaction_type,
                content=filtered_message,
                response=filtered_response,
                language=language,
                sentiment=sentiment,
                context=json.dumps({
                    "memories_accessed": [m.get("id") for m in relevant_memories],
                    "processing_time": time.time() - start_time
                })
            )

            self.db.add(interaction)
            self.db.commit()

            # Store important information as memories
            if sentiment in ["positive", "negative"] or "?" in request.message:
                await self.memory_service.store_memory(
                    family_id=context.family_id,
                    category="interaction",
                    title=f"Interacción con {context.member_name}",
                    content=request.message,
                    importance=7 if sentiment == "positive" else 5,
                    metadata={
                        "member_id": context.member_id,
                        "member_role": context.member_role,
                        "sentiment": sentiment,
                        "language": language
                    }
                )

            processing_time = time.time() - start_time

            return InteractionResponse(
                response=filtered_response,
                interaction_id=interaction_id,
                timestamp=timestamp,
                language=language,
                sentiment=sentiment,
                memories_accessed=[m.get("id") for m in relevant_memories],
                follow_up_suggestions=follow_up_suggestions,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Interaction processing failed: {e}")
            raise

    async def get_conversation_history(
        self,
        family_id: str,
        member_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a family or specific member."""
        try:
            query = self.db.query(FamilyInteraction).filter(
                FamilyInteraction.family_id == family_id
            )

            if member_id:
                query = query.filter(FamilyInteraction.family_member_id == member_id)

            interactions = query.order_by(
                FamilyInteraction.timestamp.desc()
            ).limit(limit).all()

            return [
                {
                    "id": interaction.id,
                    "member_id": interaction.family_member_id,
                    "type": interaction.interaction_type,
                    "content": interaction.content,
                    "response": interaction.response,
                    "timestamp": interaction.timestamp,
                    "language": interaction.language,
                    "sentiment": interaction.sentiment
                }
                for interaction in interactions
            ]

        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []

    async def get_family_summary(self, family_id: str) -> Dict[str, Any]:
        """Get summary of family interactions and insights."""
        try:
            # Get recent interactions
            recent_interactions = await self.get_conversation_history(family_id, limit=50)

            # Calculate statistics
            total_interactions = len(recent_interactions)
            sentiments = [i["sentiment"] for i in recent_interactions]
            languages = [i["language"] for i in recent_interactions]

            sentiment_counts = {
                "positive": sentiments.count("positive"),
                "neutral": sentiments.count("neutral"),
                "negative": sentiments.count("negative")
            }

            language_counts = {
                "es": languages.count("es"),
                "en": languages.count("en")
            }

            # Get active members
            active_members = list(set(i["member_id"] for i in recent_interactions))

            return {
                "family_id": family_id,
                "total_interactions": total_interactions,
                "sentiment_distribution": sentiment_counts,
                "language_distribution": language_counts,
                "active_members": len(active_members),
                "last_interaction": recent_interactions[0]["timestamp"] if recent_interactions else None
            }

        except Exception as e:
            logger.error(f"Failed to get family summary: {e}")
            return {}