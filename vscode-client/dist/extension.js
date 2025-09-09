var g=Object.create;var r=Object.defineProperty;var w=Object.getOwnPropertyDescriptor;var $=Object.getOwnPropertyNames;var P=Object.getPrototypeOf,y=Object.prototype.hasOwnProperty;var E=(e,n)=>{for(var t in n)r(e,t,{get:n[t],enumerable:!0})},v=(e,n,t,a)=>{if(n&&typeof n=="object"||typeof n=="function")for(let o of $(n))!y.call(e,o)&&o!==t&&r(e,o,{get:()=>n[o],enumerable:!(a=w(n,o))||a.enumerable});return e};var x=(e,n,t)=>(t=e!=null?g(P(e)):{},v(n||!e||!e.__esModule?r(t,"default",{value:e,enumerable:!0}):t,e)),R=e=>v(r({},"__esModule",{value:!0}),e);var T={};E(T,{activate:()=>b,deactivate:()=>F});module.exports=R(T);var s=x(require("vscode")),C=require("child_process"),k=x(require("path"));function b(e){let n=async(a,o,c,j)=>{let i=k.resolve(e.extensionPath,"../client/mem0");c.markdown(`> Executing: ${i} ${a.prompt}

`);let[d,...h]=a.prompt.trim().split(/\s+/),m;d==="remember"?m=[h.join(" ")]:m=h;try{let p=(0,C.execFile)(i,[d,...m],(l,u,f)=>{if(c.markdown(`**stdout:**
\`\`\`
${u}
\`\`\``),c.markdown(`**stderr:**
\`\`\`
${f}
\`\`\``),l){c.markdown(`**Error:**
\`\`\`
${l.message}
\`\`\``);return}})}catch(p){c.markdown(`**Failed to execute mem0 command:**
\`\`\`
${p.message}
\`\`\``)}return{commands:[]}},t=s.chat.createChatParticipant("mem0",n);t.iconPath=new s.ThemeIcon("beaker")}function F(){}0&&(module.exports={activate,deactivate});
