const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('serving/nano-chat/index.html','utf8');
const source=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].find(m=>m[1].includes('const voiceStatus='))[1];
const elements={};function element(id){return elements[id]??={value:'en-IN',textContent:'',disabled:false,options:[{text:'English'}],selectedIndex:0};}
let spoken,aborted=false;
class Recognition{start(){this.onstart()}abort(){aborted=true;this.onend?.()}}
const ctx={document:{querySelector:element,querySelectorAll:()=>[],addEventListener(){}},window:{SpeechRecognition:Recognition,SpeechSynthesisUtterance:function(text){this.text=text},addEventListener(){}},messages:[],input:{value:'',focus(){}},setTimeout:()=>1,clearTimeout(){}};
ctx.speechSynthesis=ctx.window.speechSynthesis={cancel(){},getVoices:()=>[{lang:'en-IN'}],speak(u){spoken=u;u.onstart();u.onend()}};ctx.SpeechSynthesisUtterance=ctx.window.SpeechSynthesisUtterance;
vm.createContext(ctx);vm.runInContext(source,ctx);
element('#readReply').onclick();assert.match(element('#voiceStatus').textContent,/Send a message first/);
vm.runInContext("readReply('Hello')",ctx);assert.equal(spoken.text,'Hello');assert.equal(element('#voiceStatus').textContent,'Finished speaking.');
element('#voiceLang').value='kn-IN';vm.runInContext("readReply('ನಮಸ್ಕಾರ')",ctx);assert.match(element('#voiceStatus').textContent,/No .* voice is installed/);
element('#dictate').onclick();assert.equal(element('#dictate').textContent,'Stop listening');
vm.runInContext("recognition.onresult({results:[[{transcript:'hello students'}]]})",ctx);assert.equal(ctx.input.value,'hello students');
vm.runInContext("recognition.onerror({error:'not-allowed'})",ctx);assert.match(element('#voiceStatus').textContent,/permission denied/);
element('#stopVoice').onclick();assert(aborted);assert.equal(element('#voiceStatus').textContent,'Voice stopped.');
console.log('PASS: no-reply guard, playback callbacks, missing voice, recognition startup/transcript/error, stop. Mocked browser APIs; not acoustic recognition verification.');
