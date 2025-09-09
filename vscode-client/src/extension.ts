import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {

    const handler: vscode.ChatRequestHandler = async (request: vscode.ChatRequest, context: vscode.ChatContext, stream: vscode.ChatResponseStream, token: vscode.CancellationToken): Promise<any> => {
        stream.markdown(`You said: ${request.prompt}`)
        return { commands: [] };
    };

    const agent = vscode.chat.createChatParticipant('mem0', handler);
    agent.iconPath = new vscode.ThemeIcon('beaker');
}

export function deactivate() {}

