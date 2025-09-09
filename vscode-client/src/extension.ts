import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';
import * as os from 'os';

export function activate(context: vscode.ExtensionContext) {

    const handler: vscode.ChatRequestHandler = (request: vscode.ChatRequest, chatContext: vscode.ChatContext, stream: vscode.ChatResponseStream, token: vscode.CancellationToken): Thenable<any> => {
        
        return new Promise<any>((resolve) => {
            try {
                const projectRoot = vscode.workspace.getConfiguration('mem0').get<string>('projectRoot');
                if (!projectRoot) {
                    stream.markdown("**Error:** Please set the `mem0.projectRoot` setting to the absolute path of your mem0 project.");
                    return resolve({ commands: [] });
                }

                const mem0CliPath = path.resolve(projectRoot, 'client/mem0');
                const [command, ...rest] = request.prompt.trim().split(/\s+/);
                let args: string[];

                if (command === 'remember') {
                    args = [rest.join(' ')];
                } else if (command === 'recall') {
                    args = []; // Recall takes no arguments
                } else {
                    args = rest;
                }

                const child = spawn(mem0CliPath, [command, ...args], { cwd: projectRoot });

                child.stdout.on('data', (data) => {
                    stream.markdown(data.toString());
                });

                child.stderr.on('data', (data) => {
                    stream.markdown(`**Error:**\n\`\`\`\n${data.toString()}\n\`\`\``);
                });

                child.on('close', (code) => {
                    resolve({ commands: [] });
                });
            } catch (err: any) {
                stream.markdown(`**Failed to execute mem0 command:**\n\`\`\`\n${err.message}\n\`\`\``);
                resolve({ commands: [] });
            }
        });
    };

    const agent = vscode.chat.createChatParticipant('mem0', handler);
    agent.iconPath = new vscode.ThemeIcon('beaker');
}

export function deactivate() {}

