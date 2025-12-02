#!/usr/bin/env python3
"""
JWT Authentication System Test

Simple test script to verify JWT authentication endpoints work correctly.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


class JWTAuthTest:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None

    async def test_authentication_flow(self) -> Dict[str, Any]:
        """Test the complete JWT authentication flow"""
        print("🔐 Testing JWT Authentication Flow...")
        results = {}

        async with aiohttp.ClientSession() as session:
            try:
                # Test 1: Health check (public endpoint)
                print("\n1. Testing public health endpoint...")
                async with session.get(f"{self.base_url}/health") as resp:
                    results["health_check"] = {
                        "status": resp.status,
                        "success": resp.status == 200
                    }
                    print(f"   Health check: {resp.status} ✅" if resp.status == 200 else f"   Health check: {resp.status} ❌")

                # Test 2: Login with default user
                print("\n2. Testing login endpoint...")
                login_data = {
                    "email": "admin@family.local",
                    "password": "family123"  # Default password for demo
                }

                async with session.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json=login_data
                ) as resp:
                    login_result = await resp.json()
                    results["login"] = {
                        "status": resp.status,
                        "success": resp.status == 200,
                        "has_tokens": "access_token" in login_result
                    }

                    if resp.status == 200 and "access_token" in login_result:
                        self.access_token = login_result["access_token"]
                        self.refresh_token = login_result["refresh_token"]
                        print(f"   Login: {resp.status} ✅")
                        print(f"   Access token received: {len(self.access_token)} chars")
                    else:
                        print(f"   Login: {resp.status} ❌")
                        print(f"   Response: {login_result}")

                # Test 3: Access protected endpoint without token
                print("\n3. Testing protected endpoint without token...")
                async with session.get(f"{self.base_url}/api/v1/auth/me") as resp:
                    results["protected_no_token"] = {
                        "status": resp.status,
                        "success": resp.status == 401  # Should get 401
                    }
                    print(f"   Protected no token: {resp.status} {'✅' if resp.status == 401 else '❌'}")

                # Test 4: Access protected endpoint with token
                if self.access_token:
                    print("\n4. Testing protected endpoint with token...")
                    headers = {"Authorization": f"Bearer {self.access_token}"}
                    async with session.get(
                        f"{self.base_url}/api/v1/auth/me",
                        headers=headers
                    ) as resp:
                        user_result = await resp.json()
                        results["protected_with_token"] = {
                            "status": resp.status,
                            "success": resp.status == 200,
                            "has_user_data": "id" in user_result
                        }
                        print(f"   Protected with token: {resp.status} {'✅' if resp.status == 200 else '❌'}")
                        if resp.status == 200:
                            print(f"   User ID: {user_result.get('id', 'N/A')}")

                # Test 5: Token refresh
                if self.refresh_token:
                    print("\n5. Testing token refresh...")
                    refresh_data = {"refresh_token": self.refresh_token}
                    async with session.post(
                        f"{self.base_url}/api/v1/auth/refresh",
                        json=refresh_data
                    ) as resp:
                        refresh_result = await resp.json()
                        results["token_refresh"] = {
                            "status": resp.status,
                            "success": resp.status == 200,
                            "has_new_access_token": "access_token" in refresh_result
                        }
                        print(f"   Token refresh: {resp.status} {'✅' if resp.status == 200 else '❌'}")

                # Test 6: Logout
                if self.refresh_token:
                    print("\n6. Testing logout...")
                    logout_data = {"refresh_token": self.refresh_token}
                    async with session.post(
                        f"{self.base_url}/api/v1/auth/logout",
                        json=logout_data
                    ) as resp:
                        logout_result = await resp.json()
                        results["logout"] = {
                            "status": resp.status,
                            "success": resp.status == 200
                        }
                        print(f"   Logout: {resp.status} {'✅' if resp.status == 200 else '❌'}")

            except Exception as e:
                results["error"] = str(e)
                print(f"❌ Test error: {e}")

        return results

    async def test_dashboard_endpoints(self) -> Dict[str, Any]:
        """Test dashboard endpoints with authentication"""
        print("\n🎛️ Testing Dashboard Endpoints...")
        results = {}

        if not self.access_token:
            print("   No access token available, skipping dashboard tests")
            return results

        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with aiohttp.ClientSession() as session:
            try:
                # Test system health endpoint
                async with session.get(
                    f"{self.base_url}/dashboard/system-health",
                    headers=headers
                ) as resp:
                    results["system_health"] = {
                        "status": resp.status,
                        "success": resp.status == 200
                    }
                    print(f"   System health: {resp.status} {'✅' if resp.status == 200 else '❌'}")

                # Test metrics endpoint
                async with session.get(
                    f"{self.base_url}/dashboard/metrics",
                    headers=headers
                ) as resp:
                    results["metrics"] = {
                        "status": resp.status,
                        "success": resp.status == 200
                    }
                    print(f"   Metrics: {resp.status} {'✅' if resp.status == 200 else '❌'}")

                # Test services endpoint
                async with session.get(
                    f"{self.base_url}/dashboard/services",
                    headers=headers
                ) as resp:
                    results["services"] = {
                        "status": resp.status,
                        "success": resp.status == 200
                    }
                    print(f"   Services: {resp.status} {'✅' if resp.status == 200 else '❌'}")

            except Exception as e:
                results["error"] = str(e)
                print(f"   Dashboard test error: {e}")

        return results

    def print_summary(self, results: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 JWT AUTHENTICATION TEST SUMMARY")
        print("="*60)

        auth_tests = [
            ("Health Check", results.get("health_check", {})),
            ("Login", results.get("login", {})),
            ("Protected (No Token)", results.get("protected_no_token", {})),
            ("Protected (With Token)", results.get("protected_with_token", {})),
            ("Token Refresh", results.get("token_refresh", {})),
            ("Logout", results.get("logout", {}))
        ]

        print("\n🔐 Authentication Tests:")
        for test_name, test_result in auth_tests:
            status = test_result.get("status", "N/A")
            success = test_result.get("success", False)
            icon = "✅" if success else "❌"
            print(f"  {test_name:.<25} {status: <8} {icon}")

        dashboard_tests = [
            ("System Health", results.get("system_health", {})),
            ("Metrics", results.get("metrics", {})),
            ("Services", results.get("services", {}))
        ]

        print("\n🎛️ Dashboard Tests:")
        for test_name, test_result in dashboard_tests:
            status = test_result.get("status", "N/A")
            success = test_result.get("success", False)
            icon = "✅" if success else "❌"
            print(f"  {test_name:.<25} {status: <8} {icon}")

        # Overall assessment
        all_auth_results = [r.get("success", False) for r in auth_tests if "status" in str(r)]
        all_dashboard_results = [r.get("success", False) for r in dashboard_tests if "status" in str(r)]

        auth_success_rate = sum(all_auth_results) / len(all_auth_results) * 100 if all_auth_results else 0
        dashboard_success_rate = sum(all_dashboard_results) / len(all_dashboard_results) * 100 if all_dashboard_results else 0

        print(f"\n📈 Success Rates:")
        print(f"  Authentication: {auth_success_rate:.0f}%")
        print(f"  Dashboard:     {dashboard_success_rate:.0f}%")

        if auth_success_rate >= 80:
            print("\n🎉 JWT Authentication System: WORKING ✅")
        else:
            print("\n⚠️ JWT Authentication System: NEEDS ATTENTION ❌")


async def main():
    """Run JWT authentication tests"""
    print("🚀 Starting JWT Authentication System Test")
    print("="*60)

    tester = JWTAuthTest()

    # Test authentication flow
    auth_results = await tester.test_authentication_flow()

    # Test dashboard endpoints
    dashboard_results = await tester.test_dashboard_endpoints()

    # Combine all results
    all_results = {**auth_results, **dashboard_results}

    # Print summary
    tester.print_summary(all_results)


if __name__ == "__main__":
    asyncio.run(main())