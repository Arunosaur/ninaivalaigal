#!/usr/bin/env python3
"""
e^M - Ninaivalaigal Agentic Execution Engine
Exponential Memory: commands, compounding memory, exponential action
Part of Ninaivalaigal by Medhays (www.medhasys.com)
"""

import sys
import os
import json
import requests
from datetime import datetime

# Add vendor directory to path for dependencies
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'client', 'vendor'))

class Mem0Client:
    def __init__(self):
        self.base_url = "http://127.0.0.1:13370"
        self.session = requests.Session()

    def make_request(self, method, endpoint, **kwargs):
        """Make HTTP request to mem0 server"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            sys.exit(1)

    def contexts(self):
        """List all contexts with scope information"""
        response = self.make_request('GET', '/contexts')
        if response.status_code == 200:
            data = response.json()
            print("📋 Available contexts:")
            for context in data.get('contexts', []):
                status = "ACTIVE" if context.get('is_active') else "inactive"
                created = context.get('created_at', '')[:19]  # Format timestamp
                scope = context.get('scope', 'personal')
                scope_icon = {'personal': '👤', 'team': '👥', 'organization': '🏢'}.get(scope, '📁')
                print(f"  {scope_icon} {context['name']} ({scope}, {status}) - created: {created}")
        else:
            print(f"❌ Failed to get contexts: {response.text}")

    def context_active(self):
        """Show active context"""
        response = self.make_request('GET', '/context/active')
        if response.status_code == 200:
            data = response.json()
            active_context = data.get('recording_context')
            if active_context:
                print(f"🎯 Terminal context: {active_context}")
            else:
                print("📭 No active context")
        else:
            print(f"❌ Failed to get active context: {response.text}")

    def context_start(self, name, scope=None):
        """Start recording to context with optional scope"""
        params = {'context': name}
        if scope:
            params['scope'] = scope
        
        response = self.make_request('POST', '/context/start', params=params)
        if response.status_code == 200:
            print(f"✅ Now recording to context: {name}")
        else:
            print(f"❌ Failed to start context: {response.text}")

    def context_stop(self, name=None):
        """Stop recording context"""
        if name:
            response = self.make_request('POST', f'/context/stop?context={name}')
        else:
            response = self.make_request('POST', '/context/stop')

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Recording stopped for context: {data.get('message', 'Unknown')}")
        else:
            print(f"❌ Failed to stop context: {response.text}")

    def remember(self, payload, context=None):
        """Store a memory entry"""
        data = {
            "type": payload.get("type", "manual"),
            "source": payload.get("source", "cli"),
            "data": payload.get("data", {})
        }

        # Add context to the data field for the server to extract
        if context:
            data["data"]["context"] = context

        response = self.make_request('POST', '/memory', json=data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Memory entry recorded.")
        else:
            print(f"❌ Failed to record memory: {response.text}")

    def context_delete(self, names):
        """Delete one or more contexts"""
        success_count = 0
        failed_count = 0
        skipped_active = 0

        for context_name in names:
            # First check if context is active
            active_response = self.make_request('GET', '/context/active')
            if active_response.status_code == 200:
                active_result = active_response.json()
                active_context = active_result.get('recording_context', '')

                if active_context == context_name:
                    print(f"⚠️  Cannot delete active context '{context_name}' - stop it first with: mem0 context stop {context_name}")
                    skipped_active += 1
                    continue

            # Context is not active, proceed with deletion
            response = self.make_request('DELETE', f'/context/{context_name}')

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Context '{context_name}' deleted successfully")
                success_count += 1
            else:
                print(f"❌ Failed to delete context '{context_name}': {response.text}")
                failed_count += 1

        print(f"\n📊 Summary: {success_count} deleted, {failed_count} failed, {skipped_active} active contexts skipped")

    def recall(self, context=None):
        """Retrieve memories"""
        if context:
            response = self.make_request('GET', f'/memory?context={context}')
        else:
            response = self.make_request('GET', '/memory/all')

        if response.status_code == 200:
            memories = response.json()
            if isinstance(memories, list) and memories:
                print("📝 Memories:")
                for memory in memories[:10]:  # Show first 10
                    print(json.dumps(memory, indent=2))
            else:
                print("📭 No memories found")
        else:
            print(f"❌ Failed to retrieve memories: {response.text}")

    def create_context(self, name, scope="personal", description=None, team_id=None, organization_id=None):
        """Create a new context with specified scope"""
        data = {
            "name": name,
            "scope": scope,
            "description": description or f"{scope.title()} context: {name}"
        }
        
        if team_id:
            data["team_id"] = team_id
        if organization_id:
            data["organization_id"] = organization_id
        
        response = self.make_request('POST', '/contexts', json=data)
        if response.status_code == 200:
            result = response.json()
            context = result.get('context', {})
            scope_icon = {'personal': '👤', 'team': '👥', 'organization': '🏢'}.get(scope, '📁')
            print(f"✅ {scope_icon} Context '{name}' created successfully ({scope} scope)")
        else:
            print(f"❌ Failed to create context: {response.text}")

def main():
    if len(sys.argv) < 2:
        print("Usage: mem0 <command> [options]")
        print("Commands: contexts, active, start, stop, delete, remember, recall, create")
        sys.exit(1)

    client = Mem0Client()
    command = sys.argv[1]

    if command == "contexts":
        client.contexts()

    elif command == "active":
        client.context_active()

    elif command == "start":
        context = None
        scope = None
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--context" and i + 1 < len(sys.argv):
                context = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--scope" and i + 1 < len(sys.argv):
                scope = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        if not context:
            print("Usage: mem0 start --context <name> [--scope personal|team|organization]")
            sys.exit(1)
        
        client.context_start(context, scope)

    elif command == "stop":
        context = None
        if len(sys.argv) >= 4 and sys.argv[2] == "--context":
            context = sys.argv[3]
        client.context_stop(context)

    elif command == "delete":
        if len(sys.argv) < 4 or sys.argv[2] != "--context":
            print("Usage: mem0 delete --context <name1> [name2] [name3] ...")
            sys.exit(1)
        
        names = sys.argv[3:]
        client.context_delete(names)

    elif command == "remember":
        if len(sys.argv) < 3:
            print("Usage: mem0 remember <json_payload> [--context <name>]")
            sys.exit(1)

        payload_str = sys.argv[2]
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            print("❌ Invalid JSON payload")
            sys.exit(1)

        context = None
        if len(sys.argv) >= 5 and sys.argv[3] == "--context":
            context = sys.argv[4]

        client.remember(payload, context)

    elif command == "recall":
        context = None
        if len(sys.argv) >= 4 and sys.argv[2] == "--context":
            context = sys.argv[3]
        client.recall(context)
    
    elif command == "create":
        if len(sys.argv) < 4 or sys.argv[2] != "--context":
            print("Usage: mem0 create --context <name> [--scope personal|team|organization] [--description <desc>] [--team-id <id>] [--org-id <id>]")
            sys.exit(1)
        
        name = sys.argv[3]
        scope = "personal"
        description = None
        team_id = None
        org_id = None
        
        i = 4
        while i < len(sys.argv):
            if sys.argv[i] == "--scope" and i + 1 < len(sys.argv):
                scope = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--description" and i + 1 < len(sys.argv):
                description = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--team-id" and i + 1 < len(sys.argv):
                team_id = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--org-id" and i + 1 < len(sys.argv):
                org_id = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        
        client.create_context(name, scope, description, team_id, org_id)


    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: contexts, active, start, stop, delete, remember, recall, create")

if __name__ == "__main__":
    main()
