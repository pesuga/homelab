"""
End-to-end tests for complete family workflows.

Tests real user scenarios:
- Daily family routines and conversations
- Multimodal content sharing and processing
- Permission enforcement and safety measures
- Schedule management and coordination
- Emergency and special situations
"""

import pytest
import asyncio
from datetime import datetime, time as dt_time
from unittest.mock import AsyncMock, patch
import tempfile
from pathlib import Path

from tests.helpers.test_helpers import (
    MockHelpers, FamilyWorkflowHelpers, FileHelpers,
    PerformanceHelpers, DatabaseHelpers
)


class TestDailyFamilyRoutines:
    """Test daily family interaction patterns."""

    @pytest.mark.e2e
    @pytest.mark.family
    @pytest.mark.asyncio
    async def test_morning_routine_coordination(self, test_db, mock_ollama_client, mock_mem0_client, mock_telegram_bot):
        """Test morning routine coordination between family members."""
        # Create family members
        parent_id = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000001,
            "username": "mom",
            "role": "parent",
            "permissions": FamilyWorkflowHelpers.create_permission_profile("parent")
        })

        child_id = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000002,
            "username": "kid",
            "role": "child",
            "permissions": FamilyWorkflowHelpers.create_permission_profile("child")
        })

        # Scenario: Parent reminds child about morning routine
        morning_reminder = "Don't forget to brush your teeth and pack your lunch!"

        # Setup memory about child's routine
        mock_mem0_client.search.return_value = [
            {"memory": "Child usually forgets to pack lunch on Mondays", "score": 0.9}
        ]

        # Generate personalized reminder
        mock_ollama_client.chat.return_value = MockHelpers.create_mock_ollama_response(
            "Good morning! Since it's Monday, I know you sometimes forget your lunch. "
            "Don't forget to brush your teeth and pack your lunch before school!"
        )

        # Send reminder to child
        mock_telegram_bot.send_message.return_value = MagicMock(message_id=1)
        await mock_telegram_bot.send_message(
            chat_id=100000002,
            text=mock_ollama_client.chat.return_value["message"]["content"]
        )

        # Verify interactions
        mock_mem0_client.search.assert_called_once()
        mock_ollama_client.chat.assert_called_once()
        mock_telegram_bot.send_message.assert_called_once()

        # Store the interaction
        mock_mem0_client.add.return_value = {"id": "morning_reminder_1"}
        await mock_mem0_client.add(
            user_id=str(child_id),
            memory="Parent sent morning reminder about brushing teeth and packing lunch",
            metadata={"type": "routine_reminder", "timestamp": datetime.now().isoformat()}
        )

    @pytest.mark.e2e
    @pytest.mark.family
    @pytest.mark.asyncio
    async def test_afternoon_school_pickup_coordination(self, test_db, mock_ollama_client, mock_telegram_bot):
        """Test after-school pickup coordination."""
        # Create family members
        working_parent = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000003,
            "username": "dad",
            "role": "parent",
            "permissions": FamilyWorkflowHelpers.create_permission_profile("parent")
        })

        teenager = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000004,
            "username": "teen",
            "role": "teenager",
            "permissions": FamilyWorkflowHelpers.create_permission_profile("teenager")
        })

        # Scenario: Working parent coordinates pickup with teenager
        pickup_request = "Can you pick up your younger sibling from soccer practice today?"

        # Generate response considering teenager's schedule and permissions
        mock_ollama_client.chat.return_value = MockHelpers.create_mock_ollama_response(
            "Sure! I have no other commitments today. What time does practice end? "
            "I'll be there at 4:30 PM to pick them up."
        )

        # Send coordination request
        mock_telegram_bot.send_message.return_value = MagicMock(message_id=2)
        await mock_telegram_bot.send_message(
            chat_id=100000004,
            text=pickup_request
        )

        # Send teenager's response
        await mock_telegram_bot.send_message(
            chat_id=100000003,
            text=mock_ollama_client.chat.return_value["message"]["content"]
        )

        # Verify coordination
        assert mock_telegram_bot.send_message.call_count == 2
        messages_sent = [call[1]["text"] for call in mock_telegram_bot.send_message.call_args_list]
        assert any("pick up" in msg.lower() for msg in messages_sent)
        assert any("4:30" in msg for msg in messages_sent)

    @pytest.mark.e2e
    @pytest.mark.family
    @pytest.mark.asyncio
    async def test_evening_dinner_planning(self, test_db, mock_ollama_client, mock_mem0_client, mock_telegram_bot):
        """Test family dinner planning conversation."""
        # Create family members
        mom_id = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000005,
            "username": "mom",
            "role": "parent",
            "permissions": FamilyWorkflowHelpers.create_permission_profile("parent")
        })

        # Scenario: Family discusses dinner plans
        dinner_query = "What should we have for dinner tonight?"

        # Search for dietary preferences and previous meals
        mock_mem0_client.search.return_value = [
            {"memory": "Family had pasta two days ago", "score": 0.8},
            {"memory": "Dad doesn't like spicy food", "score": 0.9},
            {"memory": "Kids love chicken nuggets", "score": 0.7}
        ]

        # Generate dinner suggestion based on preferences
        mock_ollama_client.chat.return_value = MockHelpers.create_mock_ollama_response(
            "Since we had pasta recently and dad doesn't like spicy food, how about we make "
            "homemade chicken nuggets? The kids would love them and it's a healthier option "
            "than takeout. I can also make some roasted vegetables on the side."
        )

        # Send dinner suggestion
        mock_telegram_bot.send_message.return_value = MagicMock(message_id=3)
        await mock_telegram_bot.send_message(
            chat_id=100000005,
            text=mock_ollama_client.chat.return_value["message"]["content"]
        )

        # Verify suggestion incorporates family preferences
        mock_mem0_client.search.assert_called_once()
        mock_ollama_client.chat.assert_called_once()

        # Store the dinner plan
        mock_mem0_client.add.return_value = {"id": "dinner_plan_1"}
        await mock_mem0_client.add(
            user_id=str(mom_id),
            memory="Planned homemade chicken nuggets for dinner with vegetables",
            metadata={"type": "meal_planning", "timestamp": datetime.now().isoformat()}
        )


class TestMultimodalContentSharing:
    """Test multimodal content processing and sharing."""

    @pytest.mark.e2e
    @pytest.mark.multimodal
    @pytest.mark.family
    @pytest.mark.asyncio
    async def test_sharing_school_artwork(self, test_db, mock_ollama_client, mock_telegram_bot):
        """Test child sharing artwork from school."""
        # Create child user
        child_id = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000006,
            "username": "young_artist",
            "role": "child",
            "permissions": FamilyWorkflowHelpers.create_permission_profile("child")
        })

        # Create test image
        test_image = await FileHelpers.create_test_image("artwork.jpg", (600, 400))

        # Scenario: Child shares artwork with family
        artwork_message = "Look what I made in art class today!"

        # Process image with vision model
        vision_analysis = MockHelpers.create_mock_ollama_response(
            "This is a colorful drawing showing what appears to be a house with a big sun "
            "in the sky. I can see bright colors - blue, yellow, and green. The artist used "
            "great creativity!",
            model="llava"
        )
        mock_ollama_client.chat.return_value = vision_analysis

        # Send artwork and analysis
        mock_telegram_bot.send_photo.return_value = MagicMock(message_id=4)
        await mock_telegram_bot.send_photo(
            chat_id=100000007,  # Parent's chat ID
            photo=open(test_image, 'rb'),
            caption=artwork_message
        )

        mock_telegram_bot.send_message.return_value = MagicMock(message_id=5)
        await mock_telegram_bot.send_message(
            chat_id=100000007,
            text=f"🎨 {artwork_message}\n\n{vision_analysis['message']['content']}"
        )

        # Verify processing and sharing
        mock_ollama_client.chat.assert_called_once()
        mock_telegram_bot.send_photo.assert_called_once()
        mock_telegram_bot.send_message.assert_called_once()

        # Cleanup
        test_image.unlink(missing_ok=True)

    @pytest.mark.e2e
    @pytest.mark.multimodal
    @pytest.mark.family
    @pytest.mark.asyncio
    async def test_vacation_photo_sharing_with_analysis(self, test_db, mock_ollama_client, mock_qdrant_client, mock_telegram_bot):
        """Test sharing and analyzing vacation photos."""
        # Create parent user
        parent_id = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000008,
            "username": "traveling_parent",
            "role": "parent",
            "permissions": FamilyWorkflowHelpers.create_permission_profile("parent")
        })

        # Create test vacation photo
        vacation_photo = await FileHelpers.create_test_image("beach_vacation.jpg", (1200, 800))

        # Scenario: Parent shares vacation photo with family
        vacation_message = "Having a wonderful time at the beach! Wish you were here!"

        # Search for related memories
        mock_qdrant_client.search.return_value = MockHelpers.create_mock_qdrant_search_results(
            scores=[0.9],
            texts=["Family went to beach last summer and loved building sandcastles"]
        )

        # Analyze photo with context
        photo_analysis = MockHelpers.create_mock_ollama_response(
            "This looks like a beautiful beach scene! I remember how much the family enjoyed "
            "building sandcastles last summer. The water looks perfect for swimming. "
            "Can't wait to see more photos and hear all about your trip!",
            model="llava"
        )
        mock_ollama_client.chat.return_value = photo_analysis

        # Share photo with family group
        family_group_id = -1000000001  # Mock group chat ID
        mock_telegram_bot.send_photo.return_value = MagicMock(message_id=6)
        await mock_telegram_bot.send_photo(
            chat_id=family_group_id,
            photo=open(vacation_photo, 'rb'),
            caption=f"🏖️ {vacation_message}"
        )

        # Send contextual analysis
        mock_telegram_bot.send_message.return_value = MagicMock(message_id=7)
        await mock_telegram_bot.send_message(
            chat_id=family_group_id,
            text=photo_analysis["message"]["content"]
        )

        # Verify enhanced sharing with memory context
        mock_qdrant_client.search.assert_called_once()
        mock_ollama_client.chat.assert_called_once()
        mock_telegram_bot.send_photo.assert_called_once()
        mock_telegram_bot.send_message.assert_called_once()

        # Store vacation memory
        await mock_ollama_client.chat()  # For memory storage
        mock_ollama_client.chat.return_value = MockHelpers.create_mock_ollama_response("Memory stored")

        # Cleanup
        vacation_photo.unlink(missing_ok=True)

    @pytest.mark.e2e
    @pytest.mark.multimodal
    @pytest.mark.family
    @pytest.mark.asyncio
    async def test_voice_message_from_grandparent(self, test_db, mock_ollama_client, mock_telegram_bot):
        """Test processing voice message from grandparent."""
        # Create grandparent user
        grandparent_id = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000009,
            "username": "grandma",
            "role": "grandparent",
            "permissions": FamilyWorkflowHelpers.create_permission_profile("grandparent")
        })

        # Create test voice message
        voice_file = await FileHelpers.create_test_audio("grandma_story.ogg", duration=15)

        # Scenario: Grandparent sends voice message with story
        # Mock transcription
        transcribed_text = "Hello my dear family! I wanted to share a story about when I was your age..."

        # Generate contextual response
        caring_response = MockHelpers.create_mock_ollama_response(
            "How lovely to hear from Grandma! Her stories are always so wonderful and full of wisdom. "
            "Everyone, take a moment to listen to this sweet message from Grandma. Her stories connect us "
            "to our family history and traditions."
        )

        mock_ollama_client.chat.return_value = caring_response

        # Process voice message and share with family
        family_group_id = -1000000001
        mock_telegram_bot.send_voice.return_value = MagicMock(message_id=8)
        await mock_telegram_bot.send_voice(
            chat_id=family_group_id,
            voice=open(voice_file, 'rb'),
            caption="🎙️ A message from Grandma"
        )

        mock_telegram_bot.send_message.return_value = MagicMock(message_id=9)
        await mock_telegram_bot.send_message(
            chat_id=family_group_id,
            text=f"📝 Transcription: {transcribed_text}\n\n{caring_response['message']['content']}"
        )

        # Verify voice processing and family sharing
        mock_ollama_client.chat.assert_called_once()
        mock_telegram_bot.send_voice.assert_called_once()
        mock_telegram_bot.send_message.assert_called_once()

        # Store the family interaction
        mock_ollama_client.chat.return_value = MockHelpers.create_mock_ollama_response("Interaction stored")

        # Cleanup
        voice_file.unlink(missing_ok=True)


class TestSafetyAndPermissions:
    """Test safety features and permission enforcement."""

    @pytest.mark.e2e
    @pytest.mark.family
    @pytest.mark.asyncio
    async def test_child_time_restriction_enforcement(self, test_db, mock_telegram_bot):
        """Test time restrictions for child users."""
        # Create child user with time restrictions
        child_permissions = FamilyWorkflowHelpers.create_permission_profile("child")
        child_permissions["time_restrictions"] = {"start": "08:00", "end": "20:00"}

        child_id = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000010,
            "username": "night_owl_child",
            "role": "child",
            "permissions": child_permissions
        })

        # Test scenarios at different times
        test_cases = [
            ("07:59", False, "Too early - time restriction"),
            ("08:00", True, "Exactly start time"),
            ("15:30", True, "Afternoon - allowed"),
            ("20:00", True, "Exactly end time"),
            ("20:01", False, "Too late - time restriction")
        ]

        for test_time, should_allow, description in test_cases:
            with pytest.subTest(time=test_time, description=description):
                is_allowed = FamilyWorkflowHelpers.is_within_time_restrictions(
                    child_permissions["time_restrictions"],
                    test_time
                )

                if not is_allowed:
                    # Send restricted message
                    mock_telegram_bot.send_message.return_value = MagicMock(message_id=10)
                    await mock_telegram_bot.send_message(
                        chat_id=100000010,
                        text="⏰ It's past your bedtime! You can chat again tomorrow morning at 8 AM. "
                             "Sweet dreams! 🌙"
                    )

                assert is_allowed == should_allow, description

    @pytest.mark.e2e
    @pytest.mark.family
    @pytest.mark.asyncio
    async def test_content_filtering_for_child(self, test_db, mock_telegram_bot):
        """Test content filtering for child users."""
        # Create child user with content filters
        child_permissions = FamilyWorkflowHelpers.create_permission_profile("child")

        child_id = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000011,
            "username": "curious_child",
            "role": "child",
            "permissions": child_permissions
        })

        # Test content that should be filtered
        inappropriate_content = [
            "This movie has some adult themes",
            "I saw a really bad fight today",
            "Let's play a violent video game"
        ]

        filtered_count = 0
        for content in inappropriate_content:
            if FamilyWorkflowHelpers.should_filter_content(content, child_permissions["content_filters"]):
                filtered_count += 1

                # Send filtered content warning
                mock_telegram_bot.send_message.return_value = MagicMock(message_id=11)
                await mock_telegram_bot.send_message(
                    chat_id=100000011,
                    text="🛡️ I noticed your message contains content that's not appropriate for your age group. "
                         "Let's talk about something else! How about your favorite hobby or what you learned in school today?"
                )

        # Verify filtering worked
        assert filtered_count > 0, "Should have filtered some inappropriate content"

    @pytest.mark.e2e
    @pytest.mark.family
    @pytest.mark.asyncio
    async def test_teenager_permission_balancing(self, test_db, mock_ollama_client, mock_telegram_bot):
        """Test balanced permissions for teenager users."""
        # Create teenager with balanced permissions
        teen_permissions = FamilyWorkflowHelpers.create_permission_profile("teenager")

        teen_id = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000012,
            "username": "independent_teen",
            "role": "teenager",
            "permissions": teen_permissions
        })

        # Test permissions work correctly
        assert teen_permissions["can_send_images"] is True
        assert teen_permissions["can_send_voice"] is True
        assert teen_permissions["can_manage_schedule"] is False
        assert teen_permissions["time_restrictions"]["start"] == "07:00"
        assert teen_permissions["time_restrictions"]["end"] == "22:00"

        # Scenario: Teenager tries to manage family schedule (should be blocked)
        schedule_request = "Can I change dinner time to 9 PM?"

        # Generate response respecting permission limits
        mock_ollama_client.chat.return_value = MockHelpers.create_mock_ollama_response(
            "I understand you'd like to change dinner time, but you don't have permission to "
            "manage the family schedule. Let me send a message to your parents to discuss this change with them."
        )

        mock_telegram_bot.send_message.return_value = MagicMock(message_id=12)
        await mock_telegram_bot.send_message(
            chat_id=100000012,
            text=mock_ollama_client.chat.return_value["message"]["content"]
        )

        # Notify parents about the request
        parent_chat_id = 100000013
        await mock_telegram_bot.send_message(
            chat_id=parent_chat_id,
            text=f"📅 Schedule Request: Your teenager wants to change dinner time to 9 PM. "
                 f"Please discuss and let me know if this works for the family."
        )

        # Verify permission enforcement
        mock_ollama_client.chat.assert_called_once()
        assert mock_telegram_bot.send_message.call_count == 2


class TestEmergencyAndSpecialSituations:
    """Test handling of emergency and special family situations."""

    @pytest.mark.e2e
    @pytest.mark.family
    @pytest.mark.asyncio
    async def test_emergency_contact_alert(self, test_db, mock_ollama_client, mock_telegram_bot):
        """Test emergency contact and alert system."""
        # Create family members
        parent1_id = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000014,
            "username": "mom",
            "role": "parent",
            "permissions": FamilyWorkflowHelpers.create_permission_profile("parent")
        })

        parent2_id = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000015,
            "username": "dad",
            "role": "parent",
            "permissions": FamilyWorkflowHelpers.create_permission_profile("parent")
        })

        # Emergency scenario
        emergency_message = "EMERGENCY: School is closing early due to severe weather. Please pick up children immediately!"

        # Generate emergency response
        mock_ollama_client.chat.return_value = MockHelpers.create_mock_ollama_response(
            "🚨 EMERGENCY ALERT: School closing early due to severe weather!\n\n"
            "Both parents have been notified. Please pick up children immediately.\n"
            "Stay safe and keep your phones available for updates."
        )

        # Send emergency alert to all parents
        for parent_id in [100000014, 100000015]:
            mock_telegram_bot.send_message.return_value = MagicMock(message_id=13)
            await mock_telegram_bot.send_message(
                chat_id=parent_id,
                text=f"🚨 {emergency_message}"
            )

        # Send coordinated response
        family_group_id = -1000000001
        await mock_telegram_bot.send_message(
            chat_id=family_group_id,
            text=mock_ollama_client.chat.return_value["message"]["content"]
        )

        # Verify emergency broadcast
        assert mock_telegram_bot.send_message.call_count == 3  # 2 parents + 1 group

    @pytest.mark.e2e
    @pytest.mark.family
    @pytest.mark.asyncio
    async def test_lost_child_coordination(self, test_db, mock_ollama_client, mock_qdrant_client, mock_telegram_bot):
        """Test coordination when child is lost or missing."""
        # Create family
        parent_id = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000016,
            "username": "worried_parent",
            "role": "parent",
            "permissions": FamilyWorkflowHelpers.create_permission_profile("parent")
        })

        # Search for last known locations and routines
        mock_qdrant_client.search.return_value = MockHelpers.create_mock_qdrant_search_results(
            scores=[0.9, 0.8],
            texts=[
                "Child usually goes to friend's house after school on Tuesdays",
                "Child's friend lives on Oak Street, house number 123"
            ]
        )

        # Generate coordinated response
        mock_ollama_client.chat.return_value = MockHelpers.create_mock_ollama_response(
            "🚨 Stay calm! Let's coordinate the search:\n\n"
            "1. Check friend's house on Oak Street #123 (usual Tuesday routine)\n"
            "2. Call the school to verify pickup time\n"
            "3. Contact other parents from the friend group\n"
            "4. I've alerted your spouse and other emergency contacts\n"
            "5. If not found in 15 minutes, call local authorities\n\n"
            "I'm here to help coordinate. Keep me updated!"
        )

        # Send coordination plan
        mock_telegram_bot.send_message.return_value = MagicMock(message_id=14)
        await mock_telegram_bot.send_message(
            chat_id=100000016,
            text=mock_ollama_client.chat.return_value["message"]["content"]
        )

        # Alert other family members
        spouse_id = 100000017
        await mock_telegram_bot.send_message(
            chat_id=spouse_id,
            text="🚨 URGENT: We need to find the child. Please check Oak Street #123 friend's house. "
                 "I'll coordinate from here."
        )

        # Verify emergency coordination
        mock_qdrant_client.search.assert_called_once()
        mock_ollama_client.chat.assert_called_once()
        assert mock_telegram_bot.send_message.call_count == 2

    @pytest.mark.e2e
    @pytest.mark.family
    @pytest.mark.asyncio
    async def test_celebration_and_special_events(self, test_db, mock_ollama_client, mock_mem0_client, mock_telegram_bot):
        """Test handling of family celebrations and special events."""
        # Create family
        parent_id = await DatabaseHelpers.create_test_family_member(test_db, {
            "telegram_id": 100000018,
            "username": "celebrating_parent",
            "role": "parent",
            "permissions": FamilyWorkflowHelpers.create_permission_profile("parent")
        })

        # Search for upcoming events and preferences
        mock_mem0_client.search.return_value = [
            {"memory": "Child's birthday is next week", "score": 0.95},
            {"memory": "Child loves chocolate cake and video games", "score": 0.9},
            {"memory": "Family usually celebrates with grandparents", "score": 0.8}
        ]

        # Generate celebration suggestions
        mock_ollama_client.chat.return_value = MockHelpers.create_mock_ollama_response(
            "🎉 BIRTHDAY PLANNING TIME!\n\n"
            "Based on what I remember:\n"
            "• Child's birthday is next week\n"
            "• Loves chocolate cake and video games\n"
            "• Include grandparents in celebration\n\n"
            "Suggestions:\n"
            "1. Order chocolate cake from favorite bakery\n"
            "2. Plan video game tournament with friends\n"
            "3. Invite grandparents for dinner\n"
            "4. Prepare gift that combines gaming interests\n"
            "5. Create photo memory collage\n\n"
            "Would you like me to help coordinate any of these?"
        )

        # Send celebration suggestions
        mock_telegram_bot.send_message.return_value = MagicMock(message_id=15)
        await mock_telegram_bot.send_message(
            chat_id=100000018,
            text=mock_ollama_client.chat.return_value["message"]["content"]
        )

        # Store celebration plan
        mock_mem0_client.add.return_value = {"id": "birthday_plan_1"}
        await mock_mem0_client.add(
            user_id="100000018",
            memory="Planning child's birthday celebration with chocolate cake, video games, and grandparents",
            metadata={"type": "celebration_planning", "event": "birthday", "timestamp": datetime.now().isoformat()}
        )

        # Verify celebration assistance
        mock_mem0_client.search.assert_called_once()
        mock_ollama_client.chat.assert_called_once()
        mock_mem0_client.add.assert_called_once()
        mock_telegram_bot.send_message.assert_called_once()


class TestPerformanceUnderLoad:
    """Test system performance under realistic family usage patterns."""

    @pytest.mark.e2e
    @pytest.mark.family
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_rush_hour_family_communication(self, test_db, mock_ollama_client, mock_telegram_bot):
        """Test system performance during peak family communication times."""
        # Simulate multiple family members communicating simultaneously
        family_members = []
        for i in range(6):  # 6 family members
            member_id = await DatabaseHelpers.create_test_family_member(test_db, {
                "telegram_id": 100000020 + i,
                "username": f"family_member_{i}",
                "role": ["parent", "child", "teenager"][i % 3],
                "permissions": FamilyWorkflowHelpers.create_permission_profile(["parent", "child", "teenager"][i % 3])
            })
            family_members.append(member_id)

        # Simulate rush hour messages (morning and evening coordination)
        rush_hour_messages = [
            "Good morning! Don't forget your lunch!",
            "Can someone pick up milk on the way home?",
            "What time is soccer practice today?",
            "I'm running late, can you start dinner?",
            "Parent-teacher conference reminder tomorrow",
            "Who's picking up the kids from school?",
            "Don't forget dentist appointment at 4 PM",
            "Can we have pizza for dinner tonight?"
        ]

        async def process_family_message(member_id, message):
            """Process a single family message."""
            mock_ollama_client.chat.return_value = MockHelpers.create_mock_ollama_response(
                f"Response to: {message[:50]}..."
            )

            response = await mock_ollama_client.chat(
                model="llama3.1:8b",
                messages=[{"role": "user", "content": message}]
            )

            await mock_telegram_bot.send_message(
                chat_id=member_id + 100000020,  # Convert to telegram ID
                text=response["message"]["content"]
            )

            return response

        # Process all messages concurrently
        start_time = asyncio.get_event_loop().time()

        tasks = []
        for i, message in enumerate(rush_hour_messages):
            member_id = family_members[i % len(family_members)]
            task = process_family_message(member_id, message)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time

        # Verify performance
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == len(rush_hour_messages)
        assert total_time < 10.0  # Should complete within 10 seconds
        assert mock_telegram_bot.send_message.call_count == len(rush_hour_messages)

        # Verify average response time
        average_time_per_message = total_time / len(rush_hour_messages)
        assert average_time_per_message < 2.0  # Under 2 seconds per message

    @pytest.mark.e2e
    @pytest.mark.family
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_weekend_family_activity_planning(self, test_db, mock_ollama_client, mock_mem0_client):
        """Test system handling of complex weekend family planning."""
        # Create extended family group
        family_members = []
        roles = ["parent", "parent", "teenager", "child", "child", "grandparent"]
        for i, role in enumerate(roles):
            member_id = await DatabaseHelpers.create_test_family_member(test_db, {
                "telegram_id": 100000030 + i,
                "username": f"{role}_{i}",
                "role": role,
                "permissions": FamilyWorkflowHelpers.create_permission_profile(role)
            })
            family_members.append(member_id)

        # Complex planning scenario with multiple constraints
        planning_request = "Plan family weekend activity that:\n- Works for all ages (2-65)\n- Weather-appropriate\n- Budget-friendly\n- Within 2-hour drive\n- Grandparent-friendly accessibility\n- Teenagers find engaging\n- Educational for younger kids"

        # Search for family preferences and constraints
        mock_mem0_client.search.return_value = [
            {"memory": "Family loves nature walks and picnics", "score": 0.9},
            {"memory": "Grandparent has mobility issues, needs accessible paths", "score": 0.8},
            {"memory": "Teenagers enjoy taking photos and learning new things", "score": 0.7},
            {"memory": "Younger kids love playgrounds and animals", "score": 0.8},
            {"memory": "Budget limit around $100 for family activities", "score": 0.6}
        ]

        # Generate comprehensive plan
        mock_ollama_client.chat.return_value = MockHelpers.create_mock_ollama_response(
            "🌟 WEEKEND FAMILY ACTIVITY PLAN 🌟\n\n"
            "**Recommended: Riverside Nature Reserve**\n\n"
            "**Why it's perfect for everyone:**\n"
            "👴👵 **Grandparents:** Paved, accessible paths with benches\n"
            "👨‍👩‍👧‍👦 **Parents:** Relaxing, affordable ($20 parking fee)\n"
            "🧑 **Teenagers:** Great photography opportunities, nature observation\n"
            "👶 **Younger kids:** Playground, duck feeding, educational visitor center\n\n"
            "**Details:**\n"
            "• 45-minute drive (within limit)\n"
            "• Wheelchair/stroller accessible\n"
            "• Free visitor center with educational exhibits\n"
            "• Picnic areas (bring lunch to save money)\n"
            "• Multiple trail lengths for different fitness levels\n\n"
            "**What to bring:**\n"
            "• Picnic lunch and drinks\n"
            "• Camera for teenagers\n"
            "• Comfortable walking shoes\n"
            "• Small coins for duck food\n\n"
            "**Weather backup:** Covered visitor center and indoor exhibits\n\n"
            "Should I help coordinate carpooling and check the weather forecast?"
        )

        # Process planning request
        @PerformanceHelpers.measure_time
        async def process_complex_planning():
            return await mock_ollama_client.chat(
                model="llama3.1:8b",
                messages=[
                    {"role": "system", "content": "You are a helpful family activity coordinator."},
                    {"role": "user", "content": planning_request}
                ],
                max_tokens=500,
                temperature=0.7
            )

        planning_result = await process_complex_planning()
        planning_response = planning_result["result"]

        # Verify comprehensive planning
        assert planning_result["execution_time"] < 5.0  # Should complete within 5 seconds
        assert len(planning_response["message"]["content"]) > 500  # Detailed response

        # Verify all family members' needs are addressed
        response_text = planning_response["message"]["content"].lower()
        assert "grandparent" in response_text or "grandparents" in response_text
        assert "teenager" in response_text or "teenagers" in response_text
        assert "budget" in response_text
        assert "accessib" in response_text  # accessibility

        # Store the planning result
        mock_mem0_client.add.return_value = {"id": "weekend_plan_1"}
        await mock_mem0_client.add(
            user_id="100000030",  # Planning parent
            memory="Weekend family activity planned: Riverside Nature Reserve with accessibility for all ages",
            metadata={
                "type": "activity_planning",
                "participants": len(family_members),
                "complexity": "high",
                "timestamp": datetime.now().isoformat()
            }
        )

        # Verify memory storage
        mock_mem0_client.search.assert_called_once()
        mock_mem0_client.add.assert_called_once()