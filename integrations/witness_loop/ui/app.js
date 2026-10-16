'use strict';
const $=id=>document.getElementById(id);
const clues={clock:['停摆时钟 · 00:17','站台留下的时间'],call:['匿名通话 · 00:17','需要证词支持'],coat:['红色雨衣纤维','询问衣服的主人'],ticket:['未使用车票','进入第二幕可见']};
let state=null,activation={state:'OFFLINE',busy:false},selected=[],nextId=0,step=1,initialized=false,locked=false;
const pending=new Map();
const errors={TURN_IN_PROGRESS:'她正在回应。可以等待，或取消当前请求。',STALE_TURN:'这次回应已经失效，案件未更新。请重新发送。',DOMAIN_ACTION_REJECTED:'这个动作暂时不能成立。检查场景、证据或输入；案件没有改变。',INVALID_ACTION_FIELDS:'请求格式无效，案件没有改变。',MODEL_REQUEST_LIMIT:'本次连接的请求预算已用完。可断开继续本地模式。',SESSION_INITIALIZATION_FAILED:'存档无法读取。请保留文件并查看本地说明；程序不会静默覆盖它。'};
function notice(text,error=false){$('notice').textContent=text;$('notice').classList.toggle('error',error)}
function show(id){if(!$(id).open)$(id).showModal()}
function close(id){if($(id).open)$(id).close()}
function request(action,params={}){
 if(!window.webkit?.messageHandlers?.hal){notice('请打开 Witness Loop.app。浏览器预览不会运行 HAL 或连接模型。',true);return Promise.reject(new Error('NATIVE_REQUIRED'))}
 const id=String(++nextId);
 return new Promise((resolve,reject)=>{pending.set(id,{resolve,reject,action});window.webkit.messageHandlers.hal.postMessage({id,action,params})});
}
window.halReceive=function(message){
 if(message.result?.activation){activation=message.result.activation;renderActivation()}
 if(message.result?.state){state=message.result.state;selected=selected.filter(x=>state.clues.includes(x));renderState(message.result)}
 const waiting=pending.get(message.id);
 if(waiting){pending.delete(message.id);if(message.ok){waiting.resolve(message.result||{})}else{const code=typeof message.error==='string'?message.error:'REQUEST_FAILED';notice(errors[code]||('操作未完成：'+code+'。状态保持不变；可重试或断开模型。'),true);waiting.reject(new Error(code))}}
 else if(!message.ok)notice(errors[message.error]||'本地运行出现问题，请查看说明。',true);
};
async function perform(action,params={}){try{return await request(action,params)}catch(_error){return null}}
function renderActivation(){
 const live=activation.state==='LIVE_VERIFIED',armed=activation.state==='ACTIVATED_UNVERIFIED';
 $('mode').textContent=live?'OpenAI · 已验证本次调用':armed?'OpenAI · 待首轮验证':'本地规则 · 模拟对白';
 $('modeDot').classList.toggle('live',live);$('budget').textContent=live||armed?`本次请求 ${activation.requests_used||0} / ${activation.request_limit||20}`:'不调用模型';
 $('activate').textContent=live||armed?'重新连接':'连接 OpenAI';$('disconnect').hidden=!(live||armed);controls();
}
function controls(){
 const busy=locked||Boolean(activation.busy),ended=Boolean(state?.ending);
 $('send').disabled=busy||ended||!state;$('ask').disabled=busy||ended||!state;
 $('cancel').hidden=!busy;
 document.querySelectorAll('[data-say]').forEach(b=>b.disabled=busy||ended||!state);
 $('advance').disabled=busy||ended||!state||state.scene>=3||(state.scene===1&&new Set(state.asked).size<2&&state.clues.length<2);
 $('link').disabled=busy||ended||selected.length!==2;
 $('verdict').disabled=busy||ended||!state||state.scene!==3||state.clues.length<2;
 $('export').disabled=busy||!state;
}
function renderState(result){
 const scenes=[['第一幕 / 雨幕站台','让她愿意留下','问案情，也可以只聊聊。自由交谈不消耗案件行动。'],['第二幕 / 证词回放','让记忆与证据相遇','她带着你们的经历来到这里。把已解锁证据连起来，也可以选择提前裁决。'],['第三幕 / 裁决室','你选择相信哪条因果链','证据和你作出的承诺会共同影响结局。没有成立的矛盾，也可以提交指控并承担后果。']];
 const current=scenes[state.scene-1];$('chapter').textContent=current[0];$('sceneTitle').textContent=current[1];$('objective').textContent=current[2];
 $('remaining').textContent=6-state.case_turns;$('trust').textContent=state.trust;$('fear').textContent=state.fear;$('trustBar').value=state.trust;$('fearBar').value=state.fear;
 for(let n=1;n<=3;n++)$('scene'+n).classList.toggle('current',n<=state.scene);
 $('dialogue').replaceChildren();
 if(!state.transcript.length){appendBubble('林雾','我只看见最后一班车离开。别把我拖进这件事。',false);appendBubble('本地模式','你可以先试试案件。要获得自由生成的角色对白，请连接 OpenAI。',false,true)}
 for(const row of state.transcript)appendBubble(row.who,row.text,row.who===state.player,row.who==='系统');
 $('dialogue').scrollTop=$('dialogue').scrollHeight;
 renderCards();$('links').replaceChildren();
 for(const pair of state.links){const row=document.createElement('div');row.className='linked';row.textContent=pair.map(id=>clues[id][0]).join(' ↔ ');$('links').append(row)}
 $('memoryList').replaceChildren();
 if(!state.memories.length){const p=document.createElement('p');p.textContent='还没有共同经历。';$('memoryList').append(p)}
 for(const memory of state.memories){const row=document.createElement('div');row.className='memory-item';const label=document.createElement('small');label.textContent=`${memory.source} · 第 ${memory.scene} 幕`;const p=document.createElement('p');p.textContent=memory.fact;row.append(label,p);$('memoryList').append(row)}
 const receipt=result.receipt;
 if(receipt?.action==='TURN_COMMITTED')$('replyMode').textContent=receipt.live_model_used?'本轮对白由 OpenAI 生成；案件变化由本地规则裁定。':'本轮对白为本地示例（模拟语言）；状态与记忆真实保存。';
 $('ending').hidden=!state.ending;
 if(state.ending){const ends={truth:['真相 · 被替换的乘客','证据链与被记住的承诺让她交出关键证词。'],partial:['灰色结局 · 案件仍未结束','证据推翻了原来的说法，但关系中的缺口仍然存在。'],false_accusation:['误判 · 把直觉当成证据','你选择了提前裁决，却没有建立可复核的矛盾链。']};const end=ends[state.ending]||['案件结束','你可以重开，再试一种交谈方式。'];$('endingTitle').textContent=end[0];$('endingText').textContent=end[1]}
 controls();
}
function appendBubble(who,text,you,system=false){const row=document.createElement('div');row.className='bubble'+(you?' you':'')+(system?' system':'');const name=document.createElement('b');name.textContent=who;const words=document.createElement('span');words.textContent=text;row.append(name,words);$('dialogue').append(row)}
function renderCards(){
 $('cards').replaceChildren();$('clueCount').textContent=state.clues.length+'/4';
 for(const [id,[title,description]] of Object.entries(clues)){
  const unlocked=state.clues.includes(id),button=document.createElement('button');button.className='card'+(!unlocked?' locked':'')+(selected.includes(id)?' selected':'');button.setAttribute('aria-pressed',String(selected.includes(id)));button.disabled=!unlocked||Boolean(state.ending)||locked||Boolean(activation.busy);button.draggable=unlocked;button.dataset.clue=id;
  const name=document.createElement('b'),desc=document.createElement('small');name.textContent=title;desc.textContent=unlocked?'已获得 · '+description:'未解锁';button.append(name,desc);button.onclick=()=>select(id);button.ondragstart=e=>e.dataTransfer.setData('text/plain',id);$('cards').append(button)
 }
 $('selection').textContent=selected.length?selected.map(x=>clues[x][0]).join(' + '):'选择两条证据';controls();
}
function select(id){if(!state||!state.clues.includes(id)||locked||activation.busy||state.ending)return;selected=selected.includes(id)?selected.filter(x=>x!==id):[...selected,id].slice(-2);renderCards()}
async function send(text){if(locked||activation.busy||!state||state.ending)return;if(!text.trim())return notice('先说点什么。');locked=true;controls();notice('林雾在听…');const result=await perform('turn',{text});locked=false;controls();if(result){$('ask').value='';notice('这一轮已经保存。')}}
$('send').onclick=()=>send($('ask').value);$('ask').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();$('send').click()}};
document.querySelectorAll('[data-say]').forEach(b=>b.onclick=()=>send(b.dataset.say));
$('activate').onclick=()=>perform('activate');$('disconnect').onclick=()=>perform('disconnect');$('cancel').onclick=async()=>{const r=await perform('cancel');if(r)notice('已取消待完成回应。已发出的请求可能仍计入提供商用量。')};
$('advance').onclick=async()=>{if(await perform('advance'))notice('场景推进，记忆保留。')};
$('link').onclick=async()=>{if(await perform('link',{clues:[...selected]})){selected=[];renderCards();notice('矛盾已成立。重复关系不会累加。')}};
$('verdict').onclick=()=>perform('verdict');$('reset').onclick=()=>perform('reset');
$('forget').onclick=()=>{if(window.confirm('删除本机保存的全部对话、承诺与案件进度，并重新开始？此操作不会删除你已导出的副本。'))perform('forget')};
$('export').onclick=()=>perform('export');$('memoryBtn').onclick=()=>show('memory');
async function developer(){const r=await perform('developer');if(!r?.developer)return;const d=r.developer;$('devReadme').textContent=d.readme;$('devSkill').textContent=Array.isArray(d.skills)?d.skills.join('\n\n'):String(d.skills);$('devManifest').textContent=JSON.stringify(d.manifest,null,2);$('devSource').textContent=d.entrypoint;show('developer')}
$('developerBtn').onclick=developer;$('chooseA').onclick=developer;$('chooseB').onclick=()=>{close('welcome');show('onboard');renderStep()};$('devPlay').onclick=()=>{close('developer');close('welcome');if(!state?.transcript.length){show('onboard');renderStep()}};
function renderStep(){for(let n=1;n<=4;n++)$('step'+n).hidden=n!==step;$('stepLabel').textContent=step+' / 4 · '+['你的身份','共享记忆','激活智能','开始案件'][step-1];$('stepTitle').textContent=['她该怎么称呼你？','记住经历，而不是编造经历','一个凭证，明确的边界','先听她说什么'][step-1];$('stepBack').hidden=step===1;$('stepNext').textContent=step===4?'进入站台':'下一步'}
$('stepBack').onclick=()=>{step=Math.max(1,step-1);renderStep()};$('stepNext').onclick=async()=>{if(step===1&&!$('player').value.trim())return notice('请填写称呼。');if(step<4){step++;renderStep();return}const r=await perform('start',{player:$('player').value.trim(),style:$('style').value});if(r){close('onboard');notice('案件开始。你可以随时连接 OpenAI，或继续体验本地示例。')}};
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>close(b.dataset.close));
$('board').ondragover=e=>e.preventDefault();$('board').ondrop=e=>{e.preventDefault();const id=e.dataTransfer.getData('text/plain');if(Object.hasOwnProperty.call(clues,id))select(id)};
document.addEventListener('keydown',e=>{if(e.key.toLowerCase()==='m'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName))show('memory')});
async function initialize(){if(initialized)return;initialized=true;const r=await perform('snapshot');if(r){notice('本地状态已恢复。只有在原生窗口确认连接后才会发出模型请求。');if(!r.state?.transcript.length&&r.state?.revision===0)show('welcome')}}
initialize();
