var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/extension.ts
var extension_exports = {};
__export(extension_exports, {
  activate: () => activate,
  deactivate: () => deactivate
});
module.exports = __toCommonJS(extension_exports);
var vscode = __toESM(require("vscode"));
var { spawn } = require("child_process");
var path = require("path");
var os = require("os");
var fs = require("fs");
function activate(context) {
  const handler = (request, chatContext, stream, token) => {
    return new Promise((resolve) => {
      let mem0CliPath;
      let projectContext;
      const workspaceConfig = vscode.workspace.getConfiguration("mem0");
      const configuredRoot = workspaceConfig.get("projectRoot");
      if (configuredRoot) {
        mem0CliPath = path.resolve(configuredRoot, "client/mem0");
      } else {
        const possiblePaths = [
          path.join(os.homedir(), "Workspace/mem0/client/mem0"),
          path.join(os.homedir(), "workspace/mem0/client/mem0"),
          path.join(os.homedir(), "Projects/mem0/client/mem0"),
          path.join(os.homedir(), "projects/mem0/client/mem0"),
          "/usr/local/bin/mem0",
          "mem0"
          // Try PATH
        ];
        mem0CliPath = possiblePaths.find((p) => {
          try {
            fs.accessSync(p);
            return true;
          } catch {
            return false;
          }
        }) || "mem0";
      }
      if (request.prompt.trim().startsWith("context ")) {
        const contextArgs = request.prompt.trim().split(/\s+/).slice(1);
        const contextCommand = contextArgs[0];
        if (contextCommand === "start" && contextArgs[1]) {
          projectContext = contextArgs[1];
          stream.markdown(`\u{1F3AF} **Started context:** \`${projectContext}\`

`);
        } else if (contextCommand === "list") {
          const child2 = spawn(mem0CliPath, ["contexts"], {
            cwd: configuredRoot || os.homedir(),
            env: { ...require("process").env }
          });
          child2.stdout.on("data", (data) => {
            stream.markdown(data.toString());
          });
          child2.stderr.on("data", (data) => {
            stream.markdown(`**Error:**
\`\`\`
${data.toString()}
\`\`\``);
          });
          child2.on("close", (code) => {
            resolve({ commands: [] });
          });
          return;
        } else if (contextCommand === "switch" && contextArgs[1]) {
          projectContext = contextArgs[1];
          stream.markdown(`\u{1F3AF} **Switched to context:** \`${projectContext}\`

`);
        } else {
          stream.markdown(`**Usage:**
- \`@mem0 context start <name>\` - Start new context
- \`@mem0 context switch <name>\` - Switch to existing context
- \`@mem0 context list\` - List all contexts

`);
          return resolve({ commands: [] });
        }
      } else {
        const workspaceConfig2 = vscode.workspace.getConfiguration("mem0");
        const explicitContext = workspaceConfig2.get("context");
        if (explicitContext) {
          projectContext = explicitContext;
          stream.markdown(`\u{1F3AF} **Context:** \`${projectContext}\` (from settings)

`);
        } else if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
          const workspaceFolder = vscode.workspace.workspaceFolders[0];
          projectContext = path.basename(workspaceFolder.uri.fsPath);
          stream.markdown(`\u{1F3AF} **Context:** \`${projectContext}\` (auto-detected from workspace)

`);
        } else {
          projectContext = "vscode-session";
          stream.markdown(`\u{1F3AF} **Context:** \`${projectContext}\` (default session)

`);
        }
      }
      if (request.prompt.trim() === "observe") {
        stream.markdown("Observing chat history...\n\n");
        for (const turn of chatContext.history) {
          if (turn instanceof vscode.ChatResponseTurn) {
            stream.markdown(`- Found a response from **@${turn.participant}**
`);
          }
        }
        return resolve({ commands: [] });
      }
      const [command, ...rest] = request.prompt.trim().split(/\s+/);
      let args;
      if (command === "remember") {
        args = [rest.join(" ")];
      } else if (command === "recall") {
        args = [];
      } else {
        args = rest;
      }
      const child = spawn(mem0CliPath, [command, ...args], {
        cwd: configuredRoot || os.homedir(),
        env: { ...require("process").env, MEM0_CONTEXT: projectContext }
      });
      child.stdout.on("data", (data) => {
        stream.markdown(data.toString());
      });
      child.stderr.on("data", (data) => {
        stream.markdown(`**Error:**
\`\`\`
${data.toString()}
\`\`\``);
      });
      child.on("close", (code) => {
        resolve({ commands: [] });
      });
    });
  };
  const agent = vscode.chat.createChatParticipant("mem0", handler);
  agent.iconPath = new vscode.ThemeIcon("beaker");
}
function deactivate() {
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  activate,
  deactivate
});
//# sourceMappingURL=extension.js.map
