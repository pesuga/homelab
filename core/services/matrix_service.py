"""
Matrix Service

Integration with Matrix Element for secure family communication and messaging.
"""

import httpx
import asyncio
import json
import hashlib
import time
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class MatrixConfig(BaseModel):
    homeserver: str = "https://matrix.org"
    bot_username: str = "familybot"
    bot_password: str
    access_token: Optional[str] = None
    device_id: str = "family-ai-device"
    room_prefix: str = "family-"
    timeout: int = 30

class MatrixRoom(BaseModel):
    room_id: str
    name: str
    topic: Optional[str] = None
    is_encrypted: bool = True
    members: List[str] = []
    family_id: str

class MatrixMessage(BaseModel):
    room_id: str
    sender: str
    content: str
    timestamp: int
    event_id: str
    message_type: str = "m.text"

class MatrixUser(BaseModel):
    user_id: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_family_member: bool = False
    family_role: Optional[str] = None

class MatrixService:
    """Service for Matrix integration and family communication."""

    def __init__(self, config: MatrixConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=self.config.homeserver,
            timeout=self.config.timeout
        )
        self.access_token = config.access_token
        self.device_id = config.device_id
        self.bot_user_id = f"@{config.bot_username}:{self._extract_server_domain()}"

    def _extract_server_domain(self) -> str:
        """Extract server domain from homeserver URL."""
        if self.config.homeserver.startswith("https://"):
            return self.config.homeserver[8:]
        elif self.config.homeserver.startswith("http://"):
            return self.config.homeserver[7:]
        return self.config.homeserver

    async def health_check(self) -> bool:
        """Check if Matrix homeserver is available."""
        try:
            response = await self.client.get("/_matrix/server/versions")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Matrix health check failed: {e}")
            return False

    async def login(self) -> str:
        """Login to Matrix and get access token."""
        try:
            login_data = {
                "type": "m.login.password",
                "user": self.config.bot_username,
                "password": self.config.bot_password,
                "device_id": self.device_id
            }

            response = await self.client.post(
                "/_matrix/client/r0/login",
                json=login_data
            )

            if response.status_code == 200:
                result = response.json()
                self.access_token = result["access_token"]
                logger.info(f"Successfully logged in as {self.config.bot_username}")
                return self.access_token
            else:
                logger.error(f"Matrix login failed: {response.status_code} - {response.text}")
                raise Exception(f"Login failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Matrix login error: {e}")
            raise

    async def create_family_room(self, family_id: str, family_name: str) -> MatrixRoom:
        """Create a private encrypted room for family communication."""
        try:
            if not self.access_token:
                await self.login()

            # Create room
            room_data = {
                "name": f"{family_name} - Family Chat",
                "topic": f"Private family room for {family_name}",
                "preset": "private_chat",
                "room_version": "9",  # Use version that supports encryption
                "initial_state": [
                    {
                        "type": "m.room.encryption",
                        "state_key": "",
                        "content": {
                            "algorithm": "m.megolm.v1.aes-sha2"
                        }
                    }
                ]
            }

            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = await self.client.post(
                "/_matrix/client/r0/createRoom",
                json=room_data,
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                room_id = result["room_id"]

                # Create room alias
                alias = f"#{self.config.room_prefix}{family_id}:{self._extract_server_domain()}"
                alias_data = {"room_id": room_id}

                alias_response = await self.client.put(
                    f"/_matrix/client/r0/directory/room/{alias}",
                    json=alias_data,
                    headers=headers
                )

                room = MatrixRoom(
                    room_id=room_id,
                    name=f"{family_name} - Family Chat",
                    topic=f"Private family room for {family_name}",
                    is_encrypted=True,
                    family_id=family_id
                )

                logger.info(f"Created family room: {room_id}")
                return room
            else:
                logger.error(f"Failed to create room: {response.status_code} - {response.text}")
                raise Exception(f"Room creation failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Matrix room creation error: {e}")
            raise

    async def invite_user_to_room(self, room_id: str, user_id: str) -> bool:
        """Invite a user to a family room."""
        try:
            if not self.access_token:
                await self.login()

            headers = {"Authorization": f"Bearer {self.access_token}"}
            invite_data = {"user_id": user_id}

            response = await self.client.post(
                f"/_matrix/client/r0/rooms/{room_id}/invite",
                json=invite_data,
                headers=headers
            )

            if response.status_code == 200:
                logger.info(f"Invited {user_id} to room {room_id}")
                return True
            else:
                logger.error(f"Failed to invite user: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Matrix invite error: {e}")
            return False

    async def send_message(self, room_id: str, message: str, msg_type: str = "m.text") -> Optional[str]:
        """Send a message to a Matrix room."""
        try:
            if not self.access_token:
                await self.login()

            # Generate transaction ID
            transaction_id = f"m{int(time.time() * 1000)}"

            message_data = {
                "msgtype": msg_type,
                "body": message
            }

            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = await self.client.put(
                f"/_matrix/client/r0/rooms/{room_id}/send/m.room.message/{transaction_id}",
                json=message_data,
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                event_id = result["event_id"]
                logger.info(f"Message sent to {room_id}: {event_id}")
                return event_id
            else:
                logger.error(f"Failed to send message: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Matrix send message error: {e}")
            return None

    async def get_room_messages(
        self,
        room_id: str,
        limit: int = 50,
        from_token: Optional[str] = None
    ) -> List[MatrixMessage]:
        """Get messages from a Matrix room."""
        try:
            if not self.access_token:
                await self.login()

            params = {
                "limit": limit,
                "dir": "b"  # Backwards (recent messages first)
            }

            if from_token:
                params["from"] = from_token

            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = await self.client.get(
                f"/_matrix/client/r0/rooms/{room_id}/messages",
                params=params,
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                events = result.get("chunk", [])

                messages = []
                for event in events:
                    if event.get("type") == "m.room.message":
                        content = event.get("content", {})
                        message = MatrixMessage(
                            room_id=room_id,
                            sender=event.get("sender", ""),
                            content=content.get("body", ""),
                            timestamp=event.get("origin_server_ts", 0),
                            event_id=event.get("event_id", ""),
                            message_type=content.get("msgtype", "m.text")
                        )
                        messages.append(message)

                return messages
            else:
                logger.error(f"Failed to get room messages: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Matrix get messages error: {e}")
            return []

    async def get_joined_rooms(self) -> List[str]:
        """Get list of rooms the bot has joined."""
        try:
            if not self.access_token:
                await self.login()

            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = await self.client.get(
                "/_matrix/client/r0/joined_rooms",
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("joined_rooms", [])
            else:
                logger.error(f"Failed to get joined rooms: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Matrix get joined rooms error: {e}")
            return []

    async def get_room_members(self, room_id: str) -> List[MatrixUser]:
        """Get members of a Matrix room."""
        try:
            if not self.access_token:
                await self.login()

            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = await self.client.get(
                f"/_matrix/client/r0/rooms/{room_id}/members",
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                events = result.get("chunk", [])

                members = []
                for event in events:
                    if event.get("type") == "m.room.member":
                        content = event.get("content", {})
                        if content.get("membership") == "join":
                            user = MatrixUser(
                                user_id=event.get("state_key", ""),
                                display_name=content.get("displayname"),
                                avatar_url=content.get("avatar_url")
                            )
                            members.append(user)

                return members
            else:
                logger.error(f"Failed to get room members: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Matrix get room members error: {e}")
            return []

    async def leave_room(self, room_id: str) -> bool:
        """Leave a Matrix room."""
        try:
            if not self.access_token:
                await self.login()

            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = await self.client.post(
                f"/_matrix/client/r0/rooms/{room_id}/leave",
                headers=headers
            )

            if response.status_code == 200:
                logger.info(f"Left room: {room_id}")
                return True
            else:
                logger.error(f"Failed to leave room: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Matrix leave room error: {e}")
            return False

    async def register_user(self, username: str, password: str) -> Optional[str]:
        """Register a new Matrix user."""
        try:
            registration_data = {
                "auth": {"type": "m.login.dummy"},
                "username": username,
                "password": password,
                "device_id": f"{username}-device"
            }

            response = await self.client.post(
                "/_matrix/client/r0/register",
                json=registration_data
            )

            if response.status_code == 200:
                result = response.json()
                user_id = result["user_id"]
                access_token = result["access_token"]
                logger.info(f"Registered user: {user_id}")
                return access_token
            else:
                logger.error(f"Failed to register user: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Matrix registration error: {e}")
            return None

    async def get_user_info(self, user_id: str) -> Optional[MatrixUser]:
        """Get information about a Matrix user."""
        try:
            if not self.access_token:
                await self.login()

            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = await self.client.get(
                f"/_matrix/client/r0/profile/{user_id}",
                headers=headers
            )

            if response.status_code == 200:
                profile = response.json()
                return MatrixUser(
                    user_id=user_id,
                    display_name=profile.get("displayname"),
                    avatar_url=profile.get("avatar_url")
                )
            else:
                logger.error(f"Failed to get user info: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Matrix get user info error: {e}")
            return None

    async def sync_messages(self, since: Optional[str] = None, timeout: int = 30000) -> Dict[str, Any]:
        """Sync messages and events from Matrix."""
        try:
            if not self.access_token:
                await self.login()

            params = {"timeout": timeout}
            if since:
                params["since"] = since

            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = await self.client.get(
                "/_matrix/client/r0/sync",
                params=params,
                headers=headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to sync: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"Matrix sync error: {e}")
            return {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()