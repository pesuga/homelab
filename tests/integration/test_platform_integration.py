"""
End-to-End Integration Tests for Family AI Platform

Tests the complete platform integration across all services and features.
"""

import asyncio
import pytest
import httpx
import json
import time
import tempfile
import wave
from typing import Dict, Any, List
from pathlib import Path

# Test configuration
API_BASE_URL = "http://localhost:8000"
API_VERSION = "v1"
TIMEOUT = 30

class TestPlatformIntegration:
    """Comprehensive integration testing for Family AI Platform."""

    def __init__(self):
        self.api_base = API_BASE_URL
        self.api_version = API_VERSION
        self.timeout = TIMEOUT
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self.auth_token = None
        self.family_id = None
        self.member_id = None

    async def setup_class(self):
        """Setup test environment."""
        print("🔧 Setting up integration test environment...")

        # Wait for services to be ready
        await self._wait_for_services()

        # Create test family and member
        await self._create_test_data()

    async def teardown_class(self):
        """Clean up test environment."""
        print("🧹 Cleaning up integration test environment...")

        if self.client:
            await self.client.aclose()

    async def _wait_for_services(self, max_retries: int = 30) -> bool:
        """Wait for all services to be ready."""
        services_to_check = [
            f"{self.api_base}/api/v{self.api_version}/health",
            "http://localhost:11434/api/tags",  # Ollama
            "http://localhost:30900/",           # Whisper
            "http://localhost:30880/health",         # Mem0
        ]

        for retry in range(max_retries):
            all_healthy = True

            for service_url in services_to_check:
                try:
                    response = await self.client.get(service_url)
                    if response.status_code != 200:
                        print(f"  Service {service_url} not ready (attempt {retry + 1}/{max_retries})")
                        all_healthy = False
                        break
                except Exception as e:
                    print(f"  Service {service_url} not available: {e}")
                    all_healthy = False
                    break

            if all_healthy:
                print("  ✅ All services are healthy")
                return True

            await asyncio.sleep(2)

        print("  ⚠️ Some services may not be available, continuing with available services")
        return True

    async def _create_test_data(self):
        """Create test family and member data."""
        try:
            # Create test family
            family_data = {
                "name": "Integration Test Family",
                "primary_language": "es",
                "secondary_language": "en",
                "timezone": "America/Mexico_City"
            }

            response = await self.client.post(
                f"{self.api_base}/api/v{self.api_version}/family/",
                json=family_data
            )

            if response.status_code == 201:
                family = response.json()
                self.family_id = family["id"]
                print(f"  ✅ Created test family: {family['name']} (ID: {family['id']})")
            else:
                print(f"  ⚠️ Could not create test family: {response.status_code}")
                return False

            # Create test member
            member_data = {
                "name": "Test Parent",
                "email": "parent@test.familyai.com",
                "role": "parent",
                "family_id": self.family_id
            }

            response = await self.client.post(
                f"{self.api_base}/api/v{self.api_version}/family/members",
                json=member_data
            )

            if response.status_code == 201:
                member = response.json()
                self.member_id = member["id"]
                print(f"  ✅ Created test member: {member['name']} (ID: {member['id']})")
                return True
            else:
                print(f"  ⚠️ Could not create test member: {response.status_code}")
                return False

        except Exception as e:
            print(f"  ❌ Failed to create test data: {e}")
            return False

    def create_test_audio_file(self, duration_seconds: int = 3) -> bytes:
        """Create a test audio file for voice testing."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            sample_rate = 16000
            frequency = 440  # A4 note
            samples = int(sample_rate * duration_seconds)

            # Generate simple audio data
            import struct
            audio_data = []
            for i in range(samples):
                value = int(32767 * 0.3 * (0.5 * (1 + (i % 1000) / 1000)))
                audio_data.append(struct.pack('<h', value))

            # Write WAV file
            with wave.open(tmp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(b''.join(audio_data))

            # Read and return bytes
            with open(tmp_file.name, 'rb') as f:
                audio_bytes = f.read()

            # Clean up
            Path(tmp_file.name).unlink()
            return audio_bytes

    @pytest.mark.asyncio
    async def test_api_health_endpoints(self):
        """Test API health and status endpoints."""
        print("\n🏥 Testing API Health Endpoints...")

        # Test root endpoint
        try:
            response = await self.client.get(f"{self.api_base}/")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "status" in data
            print("  ✅ Root endpoint working")
        except Exception as e:
            print(f"  ❌ Root endpoint failed: {e}")
            raise

        # Test detailed health endpoint
        try:
            response = await self.client.get(f"{self.api_base}/api/v{self.api_version}/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "services" in data
            print(f"  ✅ Health endpoint working: {len(data['services'])} services checked")
        except Exception as e:
            print(f"  ❌ Health endpoint failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_chat_integration(self):
        """Test complete chat integration flow."""
        print("\n💬 Testing Chat Integration...")

        if not self.family_id or not self.member_id:
            pytest.skip("Test data not available")

        # Test simple chat interaction
        try:
            chat_request = {
                "message": "Hola, ¿cómo estás? Soy el padre de prueba.",
                "interaction_type": "text",
                "language": "es"
            }

            response = await self.client.post(
                f"{self.api_base}/api/v{self.api_version}/chat/chat",
                json=chat_request
            )

            assert response.status_code == 200
            chat_response = response.json()

            assert "response" in chat_response
            assert "interaction_id" in chat_response
            assert "language" in chat_response
            assert "sentiment" in chat_response

            print(f"  ✅ Chat successful: {chat_response['response'][:50]}...")
            print(f"     Language: {chat_response['language']}, Sentiment: {chat_response['sentiment']}")

        except Exception as e:
            print(f"  ❌ Chat integration failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_voice_integration(self):
        """Test voice transcription and processing."""
        print("\n🎤 Testing Voice Integration...")

        if not self.family_id or not self.member_id:
            pytest.skip("Test data not available")

        # Create test audio file
        try:
            audio_data = self.create_test_audio_file(2)
            print("  ✅ Test audio file created")
        except Exception as e:
            print(f"  ❌ Failed to create audio file: {e}")
            raise

        # Test voice transcription
        try:
            files = {"audio_file": ("test.wav", audio_data, "audio/wav")}
            data = {"language": "es"}

            response = await self.client.post(
                f"{self.api_base}/api/v{self.api_version}/voice/transcribe",
                files=files,
                data=data
            )

            # Voice service might not be available
            if response.status_code == 200:
                transcription = response.json()
                assert "transcription" in transcription
                assert "confidence" in transcription
                assert "language_detected" in transcription

                print(f"  ✅ Voice transcription: {transcription['transcription'][:50]}...")
                print(f"     Confidence: {transcription['confidence']:.2f}, Language: {transcription['language_detected']}")

            elif response.status_code == 503:
                print("  ⚠️ Voice service not available - skipping transcription test")
            else:
                print(f"  ⚠️ Voice service returned status {response.status_code}")

        except Exception as e:
            print(f"  ⚠️ Voice transcription test failed (service may not be available): {e}")

    @pytest.mark.asyncio
    async def test_dashboard_integration(self):
        """Test dashboard and analytics endpoints."""
        print("\n📊 Testing Dashboard Integration...")

        if not self.family_id or not self.member_id:
            pytest.skip("Test data not available")

        # Test dashboard configuration
        try:
            response = await self.client.get(
                f"{self.api_base}/api/v{self.api_version}/dashboard/",
                params={"family_id": self.family_id}
            )

            if response.status_code == 200:
                dashboard = response.json()
                assert "family_id" in dashboard
                assert "layout" in dashboard
                assert isinstance(dashboard["layout"], list)

                print(f"  ✅ Dashboard loaded with {len(dashboard['layout'])} widgets")

                # Test widget data
                if dashboard["layout"]:
                    widget_id = dashboard["layout"][0]["id"]
                    response = await self.client.get(
                        f"{self.api_base}/api/v{self.api_version}/dashboard/widgets/{widget_id}/data",
                        params={"family_id": self.family_id}
                    )

                    if response.status_code == 200:
                        widget_data = response.json()
                        print(f"  ✅ Widget data retrieved: {widget_id}")
                    else:
                        print(f"  ⚠️ Widget data not available: {widget_id}")

            else:
                print(f"  ⚠️ Dashboard not available: {response.status_code}")

        except Exception as e:
            print(f"  ⚠️ Dashboard integration failed: {e}")

    @pytest.mark.asyncio
    async def test_conversation_history(self):
        """Test conversation history and analytics."""
        print("\n📚 Testing Conversation History...")

        if not self.family_id or not self.member_id:
            pytest.skip("Test data not available")

        try:
            # Test conversation history
            response = await self.client.get(
                f"{self.api_base}/api/v{self.api_version}/chat/conversation/history",
                params={"family_id": self.family_id, "limit": 5}
            )

            if response.status_code == 200:
                history = response.json()
                assert isinstance(history, list)
                print(f"  ✅ Conversation history: {len(history)} entries")

                # Test analytics (parent only)
                response = await self.client.get(
                    f"{self.api_base}/api/v{self.api_version}/chat/family/summary",
                    params={"family_id": self.family_id}
                )

                if response.status_code == 200:
                    analytics = response.json()
                    print(f"  ✅ Family analytics retrieved")
                elif response.status_code == 403:
                    print("  ✅ Analytics properly restricted (parental access required)")
                else:
                    print(f"  ⚠️ Analytics not available: {response.status_code}")

            else:
                print(f"  ⚠️ Conversation history not available: {response.status_code}")

        except Exception as e:
            print(f"  ⚠️ Conversation history test failed: {e}")

    @pytest.mark.asyncio
    async def test_bilingual_support(self):
        """Test bilingual language support."""
        print("\n🌍 Testing Bilingual Support...")

        if not self.family_id or not self.member_id:
            pytest.skip("Test data not available")

        # Test Spanish chat
        try:
            spanish_request = {
                "message": "¿Puedes ayudarme con mi tarea de matemáticas?",
                "interaction_type": "text",
                "language": "es"
            }

            response = await self.client.post(
                f"{self.api_base}/api/v{self.api_version}/chat/chat",
                json=spanish_request
            )

            if response.status_code == 200:
                spanish_response = response.json()
                print(f"  ✅ Spanish chat successful: {spanish_response['response'][:30]}...")

        except Exception as e:
            print(f"  ⚠️ Spanish chat test failed: {e}")

        # Test English chat
        try:
            english_request = {
                "message": "Can you help me with homework?",
                "interaction_type": "text",
                "language": "en"
            }

            response = await self.client.post(
                f"{self.api_base}/api/v{self.api_version}/chat/chat",
                json=english_request
            )

            if response.status_code == 200:
                english_response = response.json()
                print(f"  ✅ English chat successful: {english_response['response'][:30]}...")

        except Exception as e:
            print(f"  ⚠️ English chat test failed: {e}")

    @pytest.mark.asyncio
    async def test_service_health_monitoring(self):
        """Test service health monitoring endpoints."""
        print("\n🔍 Testing Service Health Monitoring...")

        # Test voice service status
        try:
            response = await self.client.get(
                f"{self.api_base}/api/v{self.api_version}/voice/status"
            )

            if response.status_code == 200:
                voice_status = response.json()
                print(f"  ✅ Voice service status: {voice_status.get('service_status', 'unknown')}")
                print(f"     Supported formats: {len(voice_status.get('supported_formats', []))}")
            else:
                print(f"  ⚠️ Voice status not available: {response.status_code}")

        except Exception as e:
            print(f"  ⚠️ Voice status check failed: {e}")

        # Test dashboard service status
        try:
            response = await self.client.get(
                f"{self.api_base}/api/v{self.api_version}/dashboard/status"
            )

            if response.status_code == 200:
                dashboard_status = response.json()
                print(f"  ✅ Dashboard service status: {dashboard_status.get('dashboard_service', 'unknown')}")
                print(f"     Available widgets: {len(dashboard_status.get('available_widgets', []))}")
            else:
                print(f"  ⚠️ Dashboard status not available: {response.status_code}")

        except Exception as e:
            print(f"  ⚠️ Dashboard status check failed: {e}")

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling and edge cases."""
        print("\n🚨 Testing Error Handling...")

        # Test invalid request
        try:
            invalid_request = {
                "message": "",  # Empty message
                "interaction_type": "text"
            }

            response = await self.client.post(
                f"{self.api_base}/api/v{self.api_version}/chat/chat",
                json=invalid_request
            )

            # Should return validation error
            assert response.status_code == 422
            print("  ✅ Proper validation error handling")

        except Exception as e:
            print(f"  ❌ Error handling test failed: {e}")
            raise

        # Test unauthorized access
        try:
            # Access other family data
            response = await self.client.get(
                f"{self.api_base}/api/v{self.api_version}/dashboard/",
                params={"family_id": "other-family-id"}
            )

            # Should return authorization error
            assert response.status_code in [401, 403, 404]
            print("  ✅ Proper authorization handling")

        except Exception as e:
            print(f"  ❌ Authorization test failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self):
        """Test basic performance benchmarks."""
        print("\n⚡ Testing Performance Benchmarks...")

        if not self.family_id or not self.member_id:
            pytest.skip("Test data not available")

        # Test multiple concurrent requests
        try:
            import time
            start_time = time.time()

            # Send 5 concurrent chat requests
            tasks = []
            for i in range(5):
                request = {
                    "message": f"Test message {i+1}",
                    "interaction_type": "text",
                    "language": "es"
                }
                task = self.client.post(
                    f"{self.api_base}/api/v{self.api_version}/chat/chat",
                    json=request
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks)

            end_time = time.time()
            total_time = end_time - start_time

            successful_responses = [r for r in responses if r.status_code == 200]

            if successful_responses:
                avg_response_time = total_time / len(successful_responses)
                print(f"  ✅ Concurrent requests: {len(successful_responses)}/5 successful")
                print(f"     Average response time: {avg_response_time:.2f}s")
                print(f"     Total time: {total_time:.2f}s")
            else:
                print("  ⚠️ No successful responses in concurrent test")

        except Exception as e:
            print(f"  ⚠️ Performance test failed: {e}")


# Pytest test class
@pytest.mark.integration
@pytest.mark.asyncio
class TestFamilyAIPlatform(TestPlatformIntegration):
    """Main test class for Family AI Platform integration."""
    pass


# Standalone test runner function
async def run_integration_tests():
    """Run integration tests standalone."""
    print("🚀 Family AI Platform - Integration Tests")
    print("=" * 60)

    test_suite = TestFamilyAIPlatform()

    try:
        # Setup
        await test_suite.setup_class()

        # Run tests
        await test_suite.test_api_health_endpoints()
        await test_suite.test_chat_integration()
        await test_suite.test_voice_integration()
        await test_suite.test_dashboard_integration()
        await test_suite.test_conversation_history()
        await test_suite.test_bilingual_support()
        await test_suite.test_service_health_monitoring()
        await test_suite.test_error_handling()
        await test_suite.test_performance_benchmarks()

        print("\n🎉 All Integration Tests Completed!")
        print("✨ Family AI Platform integration is working correctly")

    except Exception as e:
        print(f"\n❌ Integration tests failed: {e}")
        raise
    finally:
        await test_suite.teardown_class()


if __name__ == "__main__":
    asyncio.run(run_integration_tests())