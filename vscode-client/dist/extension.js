var q=Object.create;var C=Object.defineProperty;var y=Object.getOwnPropertyDescriptor;var E=Object.getOwnPropertyNames;var N=Object.getPrototypeOf,O=Object.prototype.hasOwnProperty;var I=(o,i)=>{for(var r in i)C(o,r,{get:i[r],enumerable:!0})},F=(o,i,r,a)=>{if(i&&typeof i=="object"||typeof i=="function")for(let m of E(i))!O.call(o,m)&&m!==r&&C(o,m,{get:()=>i[m],enumerable:!(a=y(i,m))||a.enumerable});return o};var T=(o,i,r)=>(r=o!=null?q(N(o)):{},F(i||!o||!o.__esModule?C(r,"default",{value:o,enumerable:!0}):r,o)),W=o=>F(C({},"__esModule",{value:!0}),o);var M={};I(M,{activate:()=>D,deactivate:()=>L});module.exports=W(M);var s=T(require("vscode")),{spawn:b}=require("child_process"),x=require("path"),d=require("os"),A=require("fs"),$="";function D(o){console.log("mem0 extension activating..."),s.window.showInformationMessage("mem0 extension is activating!");let i=(a,m,n,H)=>new Promise(g=>{n.markdown(`**Extension activated - processing request: "${a.prompt}"**

`);let f,c,h=s.workspace.getConfiguration("mem0").get("projectRoot");h?f=x.resolve(h,"client/mem0"):f=[x.join(d.homedir(),"Workspace/mem0/client/mem0"),x.join(d.homedir(),"workspace/mem0/client/mem0"),x.join(d.homedir(),"Projects/mem0/client/mem0"),x.join(d.homedir(),"projects/mem0/client/mem0"),"/usr/local/bin/mem0","mem0"].find(w=>{try{return A.accessSync(w),!0}catch{return!1}})||"mem0";let P=s.workspace.getConfiguration("mem0").get("context");if($)c=$;else if(P)c=P;else if(s.workspace.workspaceFolders&&s.workspace.workspaceFolders.length>0){let e=s.workspace.workspaceFolders[0];c=x.basename(e.uri.fsPath)}else c="vscode-session";if(a.prompt.trim().startsWith("context ")){let e=a.prompt.trim().split(/\s+/).slice(1),w=e[0];if(w==="start"&&e[1])$=e[1],c=$,n.markdown(`\u{1F3AF} **Started context:** \`${c}\`

`),b(f,["context","start",c],{cwd:h||d.homedir(),env:{...require("process").env}}).on("close",t=>{t===0?n.markdown(`\u2705 **Automatic recording started for context:** \`${c}\`

`):n.markdown(`\u274C **Failed to start recording for context:** \`${c}\`

`)});else if(w==="list"){let p=b(f,["contexts"],{cwd:h||d.homedir(),env:{...require("process").env}});p.stdout.on("data",t=>{n.markdown(t.toString())}),p.stderr.on("data",t=>{n.markdown(`**Error:**
\`\`\`
${t.toString()}
\`\`\``)}),p.on("close",t=>{g({commands:[]})});return}else if(w==="switch"&&e[1])c=e[1],n.markdown(`\u{1F3AF} **Switched to context:** \`${c}\`

`);else return n.markdown("**Usage:**\n- `@mem0 context start <name>` - Start new context\n- `@mem0 context switch <name>` - Switch to existing context\n- `@mem0 context list` - List all contexts\n\n"),g({commands:[]})}if(n.markdown(`\u{1F3AF} **Context:** \`${c}\`

`),a.prompt.trim()==="observe"){n.markdown(`Observing chat history...

`);for(let e of m.history)e instanceof s.ChatResponseTurn&&n.markdown(`- Found a response from **@${e.participant}**
`);return g({commands:[]})}let[k,...v]=a.prompt.trim().split(/\s+/),l;k==="remember"?l=["remember",v.join(" "),"--context",c]:k==="recall"?v.length>0?l=["recall","--context",v.join(" ")]:l=["recall","--context",c]:k==="contexts"?l=["contexts"]:l=[k,...v],n.markdown(`**Debug Info:**
`),n.markdown(`- Command: \`${f} ${l.join(" ")}\`
`),n.markdown(`- Working Directory: \`${h||d.homedir()}\`
`),n.markdown(`- Project Context: \`${c}\`

`);let S=b(f,l,{cwd:h||d.homedir(),env:{...require("process").env}}),u="",j="";S.stdout.on("data",e=>{u+=e.toString()}),S.stderr.on("data",e=>{j+=e.toString()}),S.on("close",e=>{if(n.markdown(`**Exit Code:** ${e}

`),j&&n.markdown(`**Stderr:**
\`\`\`
${j}
\`\`\`

`),u){n.markdown(`**Raw Output:**
\`\`\`json
${u}
\`\`\`

`);try{let p=u.trim().split(`
`).filter(t=>t.trim()&&!t.includes("NotOpenSSLWarning")).map(t=>JSON.parse(t));n.markdown(`**Found ${p.length} memories:**

`),p.forEach((t,R)=>{n.markdown(`${R+1}. **${t.type}** (${t.context||"no context"})
`),t.data&&t.data.text&&n.markdown(`   ${t.data.text}
`),n.markdown(`   *Created: ${t.created_at}*

`)})}catch{n.markdown(`**Formatted Output:**
${u}

`)}}else n.markdown(`**No output received**

`);g({commands:[]})})}),r=s.chat.createChatParticipant("mem0",i);r.iconPath=new s.ThemeIcon("beaker"),o.subscriptions.push(r),console.log("mem0 extension activated successfully"),s.window.showInformationMessage("mem0 extension activated successfully!")}function L(){}0&&(module.exports={activate,deactivate});
