import * as vscode from 'vscode';
import { execFile } from 'child_process';
import * as path from 'path';

export function activate(context: vscode.ExtensionContext) {

    const handler: vscode.ChatRequestHandler = async (request: vscode.ChatRequest, context: vscode.ChatContext, stream: vscode.ChatResponseStream, token: vscode.CancellationToken): Promise<any> => {
        
        const mem0CliPath = path.resolve(context.extensionPath, '../client/mem0');
        const [command, ...rest] = request.prompt.trim().split(/\s+/);
        const args = rest.join(' ');

        try {
            const child = execFile(mem0CliPath, [command, args], (error, stdout, stderr) => {
                if (error) {
                    stream.markdown(`**Error:**\n\`\`\`\n${stderr}\n\`\`\``);
                    return;
                }
                stream.markdown(stdout);
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

