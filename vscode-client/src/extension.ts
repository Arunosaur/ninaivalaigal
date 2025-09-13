import * as vscode from 'vscode';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import * as path from 'path';
import * as os from 'os';
import * as http from 'http';
import * as fs from 'fs';

// Global MCP client and context state
let mcpClient: any = null;
let currentContext: string = '';

// Initialize MCP client
async function initializeMCPClient() {
    if (mcpClient) return mcpClient;
    
    try {
        const transport = new StdioClientTransport({
            command: '/opt/homebrew/anaconda3/bin/python',
            args: ['/Users/asrajag/Workspace/mem0/server/mcp_server.py']
        });
        
        mcpClient = new Client({
            name: 'mem0-vscode',
            version: '1.0.0'
        }, {
            capabilities: {}
        });
        
        await mcpClient.connect(transport);
        return mcpClient;
    } catch (error) {
        console.error('Failed to initialize MCP client:', error);
        return null;
    }
}

export function activate(context: vscode.ExtensionContext) {
    console.log('mem0 extension activating...');
    vscode.window.showInformationMessage('mem0 extension is activating!');

    const handler: vscode.ChatRequestHandler = (request: vscode.ChatRequest, chatContext: vscode.ChatContext, stream: vscode.ChatResponseStream, token: vscode.CancellationToken): Thenable<any> => {
        
        return new Promise<any>(async (resolve) => {
            stream.markdown(`**Extension activated - processing request: "${request.prompt}"**\n\n`);
            // Initialize MCP client
            const client = await initializeMCPClient();
            if (!client) {
                stream.markdown('❌ **Failed to connect to mem0 MCP server**\n\n');
                return resolve({ commands: [] });
            }
            
            // Determine project context
            let projectContext: string;
            const workspaceConfig = vscode.workspace.getConfiguration('mem0');
            const explicitContext = workspaceConfig.get<string>('context');
            
            if (currentContext) {
                projectContext = currentContext;
            } else if (explicitContext) {
                projectContext = explicitContext;
            } else if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
                const workspaceFolder = vscode.workspace.workspaceFolders[0];
                projectContext = path.basename(workspaceFolder.uri.fsPath);
            } else {
                projectContext = 'vscode-session';
            }
            
            // Handle context selection and management
            if (request.prompt.trim().startsWith('context ')) {
                const contextArgs = request.prompt.trim().split(/\s+/).slice(1);
                const contextCommand = contextArgs[0];
                
                if (contextCommand === 'start' && contextArgs[1]) {
                    currentContext = contextArgs[1];
                    projectContext = currentContext;
                    stream.markdown(`🎯 **Started context:** \`${projectContext}\`\n\n`);
                    
                    try {
                        const result = await client.callTool({
                            name: 'context_start',
                            arguments: { context_name: projectContext }
                        });
                        stream.markdown(`✅ **${result.content[0].text}**\n\n`);
                    } catch (error: any) {
                        stream.markdown(`❌ **Failed to start context:** ${error.message}\n\n`);
                    }
                } else if (contextCommand === 'list') {
                    try {
                        const result = await client.callTool({
                            name: 'list_contexts',
                            arguments: {}
                        });
                        const contexts = result.content[0].text;
                        stream.markdown(`**Available Contexts:**\n${Array.isArray(contexts) ? contexts.join('\n') : contexts}\n\n`);
                    } catch (error: any) {
                        stream.markdown(`❌ **Failed to list contexts:** ${error.message}\n\n`);
                    }
                    return resolve({ commands: [] });
                } else if (contextCommand === 'switch' && contextArgs[1]) {
                    projectContext = contextArgs[1];
                    stream.markdown(`🎯 **Switched to context:** \`${projectContext}\`\n\n`);
                } else {
                    stream.markdown(`**Usage:**\n- \`@mem0 context start <name>\` - Start new context\n- \`@mem0 context switch <name>\` - Switch to existing context\n- \`@mem0 context list\` - List all contexts\n\n`);
                    return resolve({ commands: [] });
                }
            }
            
            // Show current context
            stream.markdown(`🎯 **Context:** \`${projectContext}\`\n\n`);

            if (request.prompt.trim() === 'observe') {
                stream.markdown("Observing chat history...\n\n");
                for (const turn of chatContext.history) {
                    if (turn instanceof vscode.ChatResponseTurn) {
                        stream.markdown(`- Found a response from **@${turn.participant}**\n`);
                    }
                }
                return resolve({ commands: [] });
            }

            const [command, ...rest] = request.prompt.trim().split(/\s+/);
            let args: string[];

            try {
                let result;
                
                if (command === 'remember') {
                    result = await client.callTool({
                        name: 'remember',
                        arguments: {
                            text: rest.join(' '),
                            context: projectContext
                        }
                    });
                    stream.markdown(`**Result:** ${result.content[0].text}\n\n`);
                } else if (command === 'recall') {
                    const contextName = rest.length > 0 ? rest.join(' ') : projectContext;
                    result = await client.callTool({
                        name: 'recall',
                        arguments: {
                            context: contextName
                        }
                    });
                    
                    const memories = result.content[0].text;
                    if (Array.isArray(memories) && memories.length > 0) {
                        stream.markdown(`**Found ${memories.length} memories:**\n\n`);
                        memories.forEach((memory, index) => {
                            stream.markdown(`${index + 1}. **${memory.type}** (${memory.context || 'no context'})\n`);
                            if (memory.data && memory.data.text) {
                                stream.markdown(`   ${memory.data.text}\n`);
                            }
                            stream.markdown(`   *Created: ${memory.created_at}*\n\n`);
                        });
                    } else {
                        stream.markdown(`**No memories found in context:** ${contextName}\n\n`);
                    }
                } else if (command === 'contexts') {
                    result = await client.callTool({
                        name: 'list_contexts',
                        arguments: {}
                    });
                    const contexts = result.content[0].text;
                    stream.markdown(`**Available Contexts:**\n${Array.isArray(contexts) ? contexts.join('\n') : contexts}\n\n`);
                } else {
                    stream.markdown(`**Unknown command:** ${command}\n\n`);
                }
            } catch (error: any) {
                stream.markdown(`❌ **Error:** ${error.message}\n\n`);
            }

            resolve({ commands: [] });
        });
    };

    const agent = vscode.chat.createChatParticipant('mem0', handler);
    agent.iconPath = new vscode.ThemeIcon('beaker');
    
    context.subscriptions.push(agent);
    console.log('mem0 extension activated successfully');
    vscode.window.showInformationMessage('mem0 extension activated successfully!');
}

export function deactivate() {}

