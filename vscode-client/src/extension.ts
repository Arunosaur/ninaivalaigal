import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';

export function activate(context: vscode.ExtensionContext) {

    const handler: vscode.ChatRequestHandler = (request: vscode.ChatRequest, chatContext: vscode.ChatContext, stream: vscode.ChatResponseStream, token: vscode.CancellationToken): Thenable<any> => {
        
        return new Promise<any>((resolve) => {
            const mem0CliPath = path.resolve(context.extensionPath, 'dist/client/mem0');
            const [command, ...rest] = request.prompt.trim().split(/\s+/);
            let args: string[];

            if (command === 'remember') {
                args = [rest.join(' ')];
            } else {
                args = rest;
            }

            const child = spawn(mem0CliPath, [command, ...args]);

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

