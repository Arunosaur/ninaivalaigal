import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';

export function activate(context: vscode.ExtensionContext) {

    const handler: vscode.ChatRequestHandler = async (request: vscode.ChatRequest, chatContext: vscode.ChatContext, stream: vscode.ChatResponseStream, token: vscode.CancellationToken): Promise<any> => {
        
        const mem0CliPath = path.resolve(context.extensionPath, 'dist/client/mem0');
        const [command, ...rest] = request.prompt.trim().split(/\s+/);
        let args: string[];

        if (command === 'remember') {
            args = [rest.join(' ')];
        } else {
            args = rest;
        }

        try {
            const child = spawn(mem0CliPath, [command, ...args]);

            child.stdout.on('data', (data) => {
                stream.markdown(data.toString());
            });

            child.stderr.on('data', (data) => {
                stream.markdown(`**Error:**\n\`\`\`\n${data.toString()}\n\`\`\``);
            });

        } catch (err: any) {
            stream.markdown(`**Failed to execute mem0 command:**\n\`\`\`\n${err.message}\n\`\`\``);
        }

        return { commands: [] };
    };

    const agent = vscode.chat.createChatParticipant('mem0', handler);
    agent.iconPath = new vscode.ThemeIcon('beaker');
}

export function deactivate() {}


