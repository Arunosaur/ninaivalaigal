#!/usr/bin/env python3
"""
Universal MCP Client for mem0
Automatically discovers and connects to mem0 server regardless of deployment method
"""

import os
import sys
import socket
import json
import subprocess
import argparse
from typing import Tuple, Optional

def get_mem0_server() -> Tuple[str, int]:
    """
    Discover mem0 server location using priority order:
    1. Environment variables
    2. Config file
    3. Service discovery (Docker/K8s)
    4. Default local
    """
    
    # 1. Environment variables (highest priority)
    host = os.getenv('NINAIVALAIGAL_SERVER_HOST')
    port = os.getenv('NINAIVALAIGAL_SERVER_PORT', '13371')
    
    if host:
        return host, int(port)
    
    # 2. Config file discovery
    config_paths = [
        os.path.expanduser('~/.mem0/config.json'),
        os.path.join(os.getcwd(), '.mem0.json'),
        '/etc/mem0/config.json'
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    return config.get('host', 'localhost'), config.get('port', 13371)
            except (json.JSONDecodeError, IOError):
                continue
    
    # 3. Service discovery
    # Kubernetes service discovery
    if os.getenv('KUBERNETES_SERVICE_HOST'):
        return 'mem0-mcp-service', 13371
    
    # Docker compose service discovery
    if os.path.exists('/.dockerenv'):
        return 'mem0-mcp', 13371
    
    # Docker network discovery
    try:
        result = subprocess.run(['docker', 'network', 'ls', '--format', '{{.Name}}'], 
                              capture_output=True, text=True, timeout=5)
        if 'mem0' in result.stdout:
            return 'mem0-mcp', 13371
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # 4. Default local development
    return 'localhost', 13371

def test_connection(host: str, port: int, timeout: int = 5) -> bool:
    """Test if mem0 server is reachable"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def create_config_file(host: str, port: int) -> None:
    """Create config file for future use"""
    config_dir = os.path.expanduser('~/.mem0')
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, 'config.json')
    config = {
        'host': host,
        'port': port,
        'created_at': '2025-09-12T16:40:00-05:00',
        'version': '1.0.0'
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def proxy_mcp_connection(host: str, port: int) -> None:
    """Proxy MCP JSON-RPC communication between IDE and mem0 server"""
    try:
        # Connect to mem0 MCP server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        
        # Set up non-blocking I/O
        sock.setblocking(False)
        
        import select
        
        while True:
            # Check for data from stdin (IDE)
            ready, _, _ = select.select([sys.stdin, sock], [], [], 1.0)
            
            if sys.stdin in ready:
                try:
                    data = sys.stdin.readline()
                    if not data:
                        break
                    sock.send(data.encode('utf-8'))
                except (BrokenPipeError, ConnectionResetError):
                    break
            
            if sock in ready:
                try:
                    response = sock.recv(4096)
                    if not response:
                        break
                    sys.stdout.write(response.decode('utf-8'))
                    sys.stdout.flush()
                except (BrokenPipeError, ConnectionResetError):
                    break
                    
    except ConnectionRefusedError:
        print(f"Error: Cannot connect to mem0 server at {host}:{port}", file=sys.stderr)
        print("Make sure the mem0 MCP server is running:", file=sys.stderr)
        print(f"  python server/mcp_server.py --host {host} --port {port}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        try:
            sock.close()
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description='Universal MCP client for mem0')
    parser.add_argument('--host', help='mem0 server host (overrides discovery)')
    parser.add_argument('--port', type=int, help='mem0 server port (overrides discovery)')
    parser.add_argument('--test', action='store_true', help='Test connection and exit')
    parser.add_argument('--config', action='store_true', help='Show current configuration')
    parser.add_argument('--save-config', action='store_true', help='Save discovered config to file')
    
    args = parser.parse_args()
    
    # Use provided host/port or discover
    if args.host and args.port:
        host, port = args.host, args.port
    else:
        host, port = get_mem0_server()
    
    # Handle special commands
    if args.config:
        print(f"mem0 server: {host}:{port}")
        config_file = os.path.expanduser('~/.mem0/config.json')
        if os.path.exists(config_file):
            print(f"Config file: {config_file}")
        else:
            print("No config file found")
        return
    
    if args.test:
        if test_connection(host, port):
            print(f"✅ mem0 server at {host}:{port} is reachable")
            sys.exit(0)
        else:
            print(f"❌ mem0 server at {host}:{port} is not reachable")
            sys.exit(1)
    
    if args.save_config:
        create_config_file(host, port)
        print(f"Config saved: {host}:{port}")
        return
    
    # Test connection before proxying
    if not test_connection(host, port):
        print(f"Warning: mem0 server at {host}:{port} is not reachable", file=sys.stderr)
        print("Attempting connection anyway...", file=sys.stderr)
    
    # Proxy MCP communication
    proxy_mcp_connection(host, port)

if __name__ == "__main__":
    main()
