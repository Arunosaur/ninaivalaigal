import * as vscode from 'vscode';
const { spawn } = require('child_process');
const path = require('path');
const os = require('os');
const fs = require('fs');

export function activate(context: vscode.ExtensionContext) {

    const handler: vscode.ChatRequestHandler = (request: vscode.ChatRequest, chatContext: vscode.ChatContext, stream: vscode.ChatResponseStream, token: vscode.CancellationToken): Thenable<any> => {
        
        return new Promise<any>((resolve) => {
            // Auto-detect mem0 installation
            let mem0CliPath: string;
            let projectContext: string;
            
            // Try workspace-specific setting first
            const initialConfig = vscode.workspace.getConfiguration('mem0');
            const configuredRoot = initialConfig.get<string>('projectRoot');
            
            if (configuredRoot) {
                mem0CliPath = path.resolve(configuredRoot, 'client/mem0');
            } else {
                // Auto-detect: look for mem0 in common locations
                const possiblePaths = [
                    path.join(os.homedir(), 'Workspace/mem0/client/mem0'),
                    path.join(os.homedir(), 'workspace/mem0/client/mem0'),
                    path.join(os.homedir(), 'Projects/mem0/client/mem0'),
                    path.join(os.homedir(), 'projects/mem0/client/mem0'),
                    '/usr/local/bin/mem0',
                    'mem0' // Try PATH
                ];
                
                mem0CliPath = possiblePaths.find(p => {
                    try {
                        fs.accessSync(p);
                        return true;
                    } catch {
                        return false;
                    }
                }) || 'mem0';
            }
            
            // Determine project context first
            const workspaceConfig = vscode.workspace.getConfiguration('mem0');
            const explicitContext = workspaceConfig.get<string>('context');
            
            if (explicitContext) {
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
                    projectContext = contextArgs[1];
                    stream.markdown(`🎯 **Started context:** \`${projectContext}\`\n\n`);
                } else if (contextCommand === 'list') {
                    // List available contexts
                    const child = spawn(mem0CliPath, ['contexts'], { 
                        cwd: configuredRoot || os.homedir(),
                        env: { ...require('process').env }
                    });
                    
                    child.stdout.on('data', (data) => {
                        stream.markdown(data.toString());
                    });
                    
                    child.stderr.on('data', (data) => {
                        stream.markdown(`**Error:**\n\`\`\`\n${data.toString()}\n\`\`\``);
                    });
                    
                    child.on('close', (code) => {
                        resolve({ commands: [] });
                    });
                    return;
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

            if (command === 'remember') {
                args = [rest.join(' '), '--context', projectContext];
            } else if (command === 'recall') {
                if (rest.length > 0) {
                    // If user specified a context like "recall CIP-analysis", use that
                    args = ['--context', rest[0]];
                } else {
                    // Default to current project context
                    args = ['--context', projectContext];
                }
            } else if (command === 'contexts') {
                args = [];
            } else {
                args = rest;
            }

            const child = spawn(mem0CliPath, [command, ...args], { 
                cwd: configuredRoot || os.homedir(),
                env: { ...require('process').env, MEM0_CONTEXT: projectContext }
            });

            child.stdout.on('data', (data) => {
                stream.markdown(data.toString());
            });

            child.stderr.on('data', (data) => {
                stream.markdown(`**Error:**\n\`\`\`\n${data.toString()}\n\`\`\``);
            });

            child.on('close', (code) => {
                resolve({ commands: [] });
            });
        });
    };

    const agent = vscode.chat.createChatParticipant('mem0', handler);
    agent.iconPath = new vscode.ThemeIcon('beaker');
}

export function deactivate() {}

