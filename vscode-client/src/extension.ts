import * as vscode from 'vscode';
import { execFile } from 'child_process';
import * as path from 'path';

export function activate(context: vscode.ExtensionContext) {

    const handler: vscode.ChatRequestHandler = async (request: vscode.ChatRequest, chatContext: vscode.ChatContext, stream: vscode.ChatResponseStream, token: vscode.CancellationToken): Promise<any> => {
        
        const mem0CliPath = path.resolve(context.extensionPath, '../client/mem0');
        stream.markdown(`> Executing: ${mem0CliPath} ${request.prompt}\n\n`);

        const [command, ...rest] = request.prompt.trim().split(/\s+/);
        let args: string[];

        if (command === 'remember') {
            args = [rest.join(' ')];
        } else {
            args = rest;
        }

        try {
            const child = execFile(mem0CliPath, [command, ...args], (error, stdout, stderr) => {
                stream.markdown(`**stdout:**\n\`\`\`\n${stdout}\n\`\`\``);
                stream.markdown(`**stderr:**\n\`\`\`\n${stderr}\n\`\`\``);
                if (error) {
                    stream.markdown(`**Error:**\n\`\`\`\n${error.message}\n\`\`\``);
                    return;
                }
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

