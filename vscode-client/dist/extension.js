var k=Object.create;var c=Object.defineProperty;var P=Object.getOwnPropertyDescriptor;var w=Object.getOwnPropertyNames;var y=Object.getPrototypeOf,g=Object.prototype.hasOwnProperty;var R=(e,t)=>{for(var n in t)c(e,n,{get:t[n],enumerable:!0})},i=(e,t,n,a)=>{if(t&&typeof t=="object"||typeof t=="function")for(let o of w(t))!g.call(e,o)&&o!==n&&c(e,o,{get:()=>t[o],enumerable:!(a=P(t,o))||a.enumerable});return e};var d=(e,t,n)=>(n=e!=null?k(y(e)):{},i(t||!e||!e.__esModule?c(n,"default",{value:e,enumerable:!0}):n,e)),q=e=>i(c({},"__esModule",{value:!0}),e);var T={};R(T,{activate:()=>E,deactivate:()=>F});module.exports=q(T);var r=d(require("vscode")),h=require("child_process"),p=d(require("path"));function E(e){let t=async(a,o,s,$)=>{let v=p.resolve(o.extensionPath,"../client/mem0"),[l,...x]=a.prompt.split(" ");try{let m=(0,h.execFile)(v,[l,...x],(C,u,f)=>{if(C){s.markdown(`**Error:**
\`\`\`
${f}
\`\`\``);return}s.markdown(u)})}catch(m){s.markdown(`**Failed to execute mem0 command:**
\`\`\`
${m.message}
\`\`\``)}return{commands:[]}},n=r.chat.createChatParticipant("mem0",t);n.iconPath=new r.ThemeIcon("beaker")}function F(){}0&&(module.exports={activate,deactivate});
