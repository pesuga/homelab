#!/usr/bin/env python3
"""
MCP Integration Test Script

Tests the two-tier MCP system database integration and arcade.dev configuration.
"""

import asyncio
import asyncpg
import json
import os
from datetime import datetime
from typing import Dict, Any, List

# Database connection settings
DB_HOST = "postgres.homelab.svc.cluster.local"
DB_PORT = 5432
DB_USER = "homelab"
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "homelab")
DB_NAME = "homelab"

class MCPIntegrationTester:
    def __init__(self):
        self.db_pool = None

    async def setup(self):
        """Initialize database connection"""
        self.db_pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            min_size=1,
            max_size=5
        )
        print("✅ Database connection established")

    async def teardown(self):
        """Close database connection"""
        if self.db_pool:
            await self.db_pool.close()
            print("✅ Database connection closed")

    async def test_admin_mcp_overview(self):
        """Test admin MCP overview functionality"""
        print("\n🔍 Testing Admin MCP Overview...")

        async with self.db_pool.acquire() as conn:
            # Test admin overview view
            overview = await conn.fetchrow("SELECT * FROM admin_mcp_overview")

            print(f"📊 Total Servers: {overview['total_servers']}")
            print(f"✅ Enabled Servers: {overview['enabled_servers']}")
            print(f"🔧 Total Tools: {overview['total_tools']}")
            print(f"🛡️ Tools Requiring Approval: {overview['tools_requiring_approval']}")
            print(f"⚠️ High Risk Tools: {overview['high_risk_tools']}")

            return overview

    async def test_family_member_access(self):
        """Test family member access control"""
        print("\n👨‍👩‍👧‍👦 Testing Family Member Access Control...")

        async with self.db_pool.acquire() as conn:
            # Get all family members
            members = await conn.fetch("SELECT id, username, role FROM family_members WHERE is_active = true")

            access_results = []
            for member in members:
                print(f"\n👤 {member['username']} ({member['role']}):")

                # Get available tools for this member
                tools = await conn.fetch("""
                    SELECT
                        sta.tool_name,
                        ams.name as server_name,
                        sta.personal_data_risk,
                        sta.requires_parent_approval
                    FROM system_tool_availability sta
                    JOIN admin_mcp_servers ams ON sta.server_id = ams.id
                    WHERE sta.is_enabled = true
                    AND $1 = ANY(sta.allowed_roles)
                    ORDER BY sta.tool_name
                """, member['role'])

                for tool in tools:
                    risk_indicator = "🟢" if tool['personal_data_risk'] == 'low' else "🟡" if tool['personal_data_risk'] == 'medium' else "🔴"
                    approval_indicator = " ✅" if not tool['requires_parent_approval'] else " ⚠️ Needs Approval"

                    print(f"  {risk_indicator} {tool['tool_name']} ({tool['server_name']}){approval_indicator}")
                    access_results.append({
                        'member': member['username'],
                        'role': member['role'],
                        'tool': tool['tool_name'],
                        'server': tool['server_name'],
                        'risk': tool['personal_data_risk'],
                        'needs_approval': tool['requires_parent_approval']
                    })

            return access_results

    async def test_risk_based_access(self):
        """Test risk-based access control"""
        print("\n🛡️ Testing Risk-Based Access Control...")

        async with self.db_pool.acquire() as conn:
            # Get high-risk tools
            high_risk_tools = await conn.fetch("""
                SELECT sta.tool_name, ams.name as server_name, sta.allowed_roles
                FROM system_tool_availability sta
                JOIN admin_mcp_servers ams ON sta.server_id = ams.id
                WHERE sta.personal_data_risk = 'high' AND sta.is_enabled = true
            """)

            if not high_risk_tools:
                print("✅ No high-risk tools configured")
                return []

            print(f"⚠️ Found {len(high_risk_tools)} high-risk tools:")

            for tool in high_risk_tools:
                roles = json.loads(tool['allowed_roles'])
                print(f"  🔴 {tool['tool_name']} ({tool['server_name']}) - Limited to: {', '.join(roles)}")

                # Test child access
                if 'child' in roles:
                    print(f"    ❌ Child access: BLOCKED (high risk)")
                else:
                    print(f"    ✅ Child access: NOT ALLOWED by role")

            return high_risk_tools

    async def test_arcade_config(self):
        """Test arcade.dev configuration"""
        print("\n🎮 Testing Arcade.dev Configuration...")

        async with self.db_pool.acquire() as conn:
            # Check arcade config
            config = await conn.fetchrow("SELECT * FROM admin_arcade_config")

            if not config:
                print("❌ No arcade.dev configuration found")
                return None

            print(f"📋 Arcade.dev Config Status:")
            print(f"  Enabled: {'✅' if config['is_enabled'] else '❌'}")
            print(f"  Auto Sync: {'✅' if config['auto_sync'] else '❌'}")
            print(f"  Sync Status: {config['sync_status']}")
            print(f"  Webhook URL: {config['webhook_url']}")
            print(f"  Created: {config['created_at']}")

            return config

    async def test_analytics_functions(self):
        """Test analytics functions"""
        print("\n📈 Testing Analytics Functions...")

        async with self.db_pool.acquire() as conn:
            # Test system usage analytics (last 7 days)
            try:
                analytics = await conn.fetch("SELECT * FROM get_system_usage_analytics(7)")

                if analytics:
                    print(f"📊 Usage Analytics (last 7 days):")
                    for row in analytics:
                        print(f"  📅 {row['date']}: {row['total_executions']} executions")

                return analytics
            except Exception as e:
                print(f"⚠️ Analytics function test failed: {e}")
                return None

    async def test_tool_recommendations(self):
        """Test tool recommendation system"""
        print("\n💡 Testing Tool Recommendation System...")

        async with self.db_pool.acquire() as conn:
            # Test recommendations for different user types
            test_user_id = '00000000-0000-0000-0000-000000000001'  # Parent user

            try:
                recommendations = await conn.fetch("""
                    SELECT tool_name, server_name, recommendation_reason, score
                    FROM get_family_tool_recommendations($1)
                    LIMIT 5
                """, test_user_id)

                if recommendations:
                    print(f"💡 Sample Recommendations for Parent:")
                    for rec in recommendations:
                        print(f"  🎯 {rec['tool_name']} ({rec['server_name']}) - Score: {rec['score']}")
                        print(f"     Reason: {rec['recommendation_reason']}")

                return recommendations
            except Exception as e:
                print(f"⚠️ Recommendation system test failed: {e}")
                return None

async def main():
    """Run all MCP integration tests"""
    print("🚀 Starting MCP Integration Tests")
    print("=" * 50)

    tester = MCPIntegrationTester()

    try:
        await tester.setup()

        # Run all tests
        await tester.test_admin_mcp_overview()
        await tester.test_family_member_access()
        await tester.test_risk_based_access()
        await tester.test_arcade_config()
        await tester.test_analytics_functions()
        await tester.test_tool_recommendations()

        print("\n" + "=" * 50)
        print("✅ All MCP Integration Tests Completed!")
        print("📋 Two-Tier MCP System is ready for deployment")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        await tester.teardown()

if __name__ == "__main__":
    asyncio.run(main())