const $ = (id) => document.getElementById(id);
const icons = { floor:'', wall:'', yellow_door:'▥', blue_door:'▥', yellow_key:'⚿', blue_key:'⚿', red_potion:'♥', blue_potion:'♥', attack_gem:'♦', defense_gem:'♦', enemy:'♟', stairs:'▲', boss:'♛' };

const messages = {
  zh: {
    title:'遗忘之塔', tagline:'让 Jev 在每一扇门前，做一次有代价的选择', jevSettings:'Jev 设置', heroName:'无名勇者',
    hp:'生命', attack:'攻击', defense:'防御', gold:'金币', yellowKey:'黄钥匙', blueKey:'蓝钥匙', keyboard:'键盘控制', orArrows:'或方向键',
    step:'Jev 决策一步', auto:'连续推演', stop:'停止推演', elapsed:'连续用时', reset:'重置', decisionSource:'决策源', localBaseline:'本地基线',
    decisionView:'Jev 决策视图', waitDecision:'等待第一次决策', probabilityHint:'概率分布会显示在这里', model:'模型', latency:'耗时',
    candidates:'当前候选', chronicle:'攀登记录', configTitle:'Jev 连接设置', keyPlaceholder:'留空则保持当前 Key', apiUrl:'API 地址', language:'界面语言',
    privacy:'Key 仅发送到本机服务并保存在当前进程内存，不会写入浏览器或项目文件。', restoreEnv:'恢复环境配置', apply:'应用配置',
    sealBroken:'封印已破', ascentComplete:'Jev 完成了这次攀登', engineReady:'引擎就绪', jevOnline:'Jev 在线决策', fallback:'Jev 不可用 · 已切换基线',
    environment:'环境变量默认配置', pageConfig:'页面临时配置', ready:'已就绪', notConfigured:'尚未配置', decisions:'次决策', avgConfidence:'平均置信度',
    configApplied:'Jev 配置已应用到当前进程', envRestored:'已恢复环境变量配置', configFailed:'配置失败', requestFailed:'请求失败',
    directions:{up:'向上', right:'向右', down:'向下', left:'向左'}
  },
  en: {
    title:'The Forgotten Tower', tagline:'Let Jev make a consequential choice at every door', jevSettings:'Jev Settings', heroName:'Nameless Hero',
    hp:'Health', attack:'Attack', defense:'Defense', gold:'Gold', yellowKey:'Yellow key', blueKey:'Blue key', keyboard:'Keyboard', orArrows:'or arrow keys',
    step:'Ask Jev', auto:'Auto Run', stop:'Stop', elapsed:'Run time', reset:'Reset', decisionSource:'Decision source', localBaseline:'Local baseline',
    decisionView:'Jev Decision View', waitDecision:'Waiting for the first decision', probabilityHint:'The probability distribution will appear here', model:'Model', latency:'Latency',
    candidates:'Current Candidates', chronicle:'Chronicle', configTitle:'Jev Connection Settings', keyPlaceholder:'Leave blank to keep the current key', apiUrl:'API URL', language:'Interface language',
    privacy:'The key is sent only to this local server and kept in process memory. It is never written to the browser or project files.', restoreEnv:'Restore environment', apply:'Apply',
    sealBroken:'The Seal Is Broken', ascentComplete:'Jev completed the ascent', engineReady:'Engine ready', jevOnline:'Jev is deciding', fallback:'Jev unavailable · baseline active',
    environment:'Environment defaults', pageConfig:'Temporary page settings', ready:'Ready', notConfigured:'Not configured', decisions:'decisions', avgConfidence:'Avg. confidence',
    configApplied:'Jev settings applied to this process', envRestored:'Environment settings restored', configFailed:'Configuration failed', requestFailed:'Request failed',
    directions:{up:'Up', right:'Right', down:'Down', left:'Left'}
  }
};

let languagePreference = localStorage.getItem('jev-language') || 'auto';
let currentLanguage = resolveLanguage(languagePreference);
let state = null;
let config = null;
let busy = false;
let autoRunning = false;
let runStartedAt = null;
let runElapsedMs = 0;
let timerFrame = null;

function t(key) { return messages[currentLanguage][key]; }
function resolveLanguage(preference) {
  if (preference === 'zh' || preference === 'en') return preference;
  const languages = navigator.languages || [navigator.language || 'en'];
  return languages.some(value => value.toLowerCase().startsWith('zh')) ? 'zh' : 'en';
}
function applyTranslations() {
  document.documentElement.lang = currentLanguage === 'zh' ? 'zh-CN' : 'en';
  document.title = `${t('title')} · Jev`;
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { el.placeholder = t(el.dataset.i18nPlaceholder); });
  renderAutoButton();
}

async function request(path, payload = {}) {
  busy = true; setControls();
  try {
    const response = await fetch(path, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...payload,lang:currentLanguage})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || t('requestFailed'));
    state = data; render(); return data;
  } catch (error) { showToast(error.message); stopAuto(); return null; }
  finally { busy = false; setControls(); }
}
async function load() { const response = await fetch(`/api/state?lang=${currentLanguage}`); state = await response.json(); render(); }
async function loadConfig() { const response = await fetch('/api/config'); config = await response.json(); renderConfig(); }
function renderConfig() {
  if (!config) return;
  $('baseUrlInput').value = config.base_url; $('modelInput').value = config.model; $('apiKeyInput').value = ''; $('languageSelect').value = languagePreference;
  const source = config.source === 'page' ? t('pageConfig') : t('environment');
  $('configSource').textContent = `${source} · Key ${config.api_key_hint} · ${config.configured ? t('ready') : t('notConfigured')}`;
}

function render() {
  const hero = state.hero;
  $('hp').textContent=hero.hp; $('attack').textContent=hero.attack; $('defense').textContent=hero.defense; $('gold').textContent=hero.gold;
  $('yellowKeys').textContent=hero.yellow_keys; $('blueKeys').textContent=hero.blue_keys;
  $('floorNumber').textContent=`FLOOR ${String(state.floor.number).padStart(2,'0')} / ${String(state.floor.total).padStart(2,'0')}`;
  $('floorName').textContent=state.floor.name; $('floorSubtitle').textContent=state.floor.subtitle; $('turn').textContent=`T${state.turn}`;
  renderBoard(); renderCandidates(); renderDecision(); renderEvents();
  $('ending').classList.toggle('hidden',!state.won);
  $('metrics').textContent=`${state.metrics.decisions} ${t('decisions')} · ${t('avgConfidence')} ${Math.round(state.metrics.average_confidence*100)}% · ${state.metrics.average_latency_ms}ms`;
  const fallback=state.decision?.mode==='fallback';
  $('engineStatus').textContent=fallback?t('fallback'):state.decision?.mode==='jev'?t('jevOnline'):t('engineReady');
  setControls();
}
function renderBoard() {
  const board=$('board'); board.innerHTML='';
  const available=new Map(state.actions.map(action=>[`${action.destination.row}:${action.destination.col}`,action]));
  state.grid.forEach((row,r)=>row.forEach((tile,c)=>{
    const el=document.createElement('div'); const action=available.get(`${r}:${c}`);
    el.className=`tile ${tile.kind}${action?' available':''}`;
    el.title=tile.enemy?`${tile.label} HP ${tile.enemy.hp} / ATK ${tile.enemy.attack} / DEF ${tile.enemy.defense}`:tile.label;
    if(state.position.row===r&&state.position.col===c){el.className='tile hero';el.textContent='♙';}
    else{el.textContent=icons[tile.kind]??tile.icon;if(tile.enemy){const stats=document.createElement('small');stats.textContent=`${tile.enemy.attack}/${tile.enemy.defense}`;el.appendChild(stats);}}
    if(action)el.onclick=()=>move(action.id);board.appendChild(el);
  }));
}
function renderCandidates() {
  $('candidateCount').textContent=state.actions.length;const root=$('candidates');root.innerHTML='';
  state.actions.forEach(action=>{const item=document.createElement('div');item.className='candidate';item.innerHTML=`<strong>${arrow(action.direction)}</strong><p><b>${t('directions')[action.direction]} · ${escapeHtml(action.tile)}</b>${escapeHtml(action.description)}</p>`;item.onclick=()=>move(action.id);root.appendChild(item);});
}
function renderDecision() {
  const decision=state.decision;$('decisionEmpty').classList.toggle('hidden',!!decision);$('probabilities').classList.toggle('hidden',!decision);
  if(!decision){$('confidenceBadge').textContent='—';$('modelName').textContent='—';$('latency').textContent='—';$('probabilities').innerHTML='';return;}
  $('confidenceBadge').textContent=`${Math.round(decision.confidence*100)}% CONF`;$('modelName').textContent=decision.model.length>36?`${decision.model.slice(0,36)}…`:decision.model;$('modelName').title=decision.model;$('latency').textContent=`${decision.latency_ms}ms`;
  const root=$('probabilities');root.innerHTML='';
  Object.entries(decision.probabilities).sort((a,b)=>b[1]-a[1]).forEach(([id,probability])=>{const row=document.createElement('div');const direction=id.replace('move_','');row.className=`probability${id===decision.action_id?' chosen':''}`;row.innerHTML=`<span class="label">${t('directions')[direction]||id}</span><span class="bar"><i style="width:${Math.max(1,probability*100)}%"></i></span><b>${Math.round(probability*100)}%</b>`;root.appendChild(row);});
}
function renderEvents(){$('events').innerHTML=state.events.map(event=>`<li>${escapeHtml(event)}</li>`).join('');}
function renderAutoButton(){$('autoButton').innerHTML=`<span>${autoRunning?'■':'▶'}</span> <span>${autoRunning?t('stop'):t('auto')}</span>`;}
function arrow(direction){return{up:'↑',right:'→',down:'↓',left:'←'}[direction];}
function escapeHtml(value){const node=document.createElement('span');node.textContent=value;return node.innerHTML;}
function move(actionId){if(!busy&&!state.won)request('/api/move',{action_id:actionId});}
async function step(){if(busy||state.won)return;const result=await request('/api/ai/step',{mode:$('engineMode').value});if(autoRunning&&result&&!state.won)step();else if(state.won||!result)stopAuto();}
function toggleAuto(){if(state?.won)return;if(autoRunning)stopAuto();else{autoRunning=true;startRunTimer();$('autoButton').classList.add('active');renderAutoButton();step();}}
function stopAuto(){autoRunning=false;$('autoButton').classList.remove('active');stopRunTimer();renderAutoButton();}
function startRunTimer(){runElapsedMs=0;runStartedAt=performance.now();$('runTimerBox').classList.add('active');updateRunTimer();}
function stopRunTimer(){if(runStartedAt!==null){runElapsedMs+=performance.now()-runStartedAt;runStartedAt=null;}if(timerFrame!==null)cancelAnimationFrame(timerFrame);timerFrame=null;$('runTimerBox').classList.remove('active');renderRunTimer();}
function resetRunTimer(){stopRunTimer();runElapsedMs=0;renderRunTimer();}
function updateRunTimer(){renderRunTimer();if(runStartedAt!==null)timerFrame=requestAnimationFrame(updateRunTimer);}
function renderRunTimer(){const elapsed=runElapsedMs+(runStartedAt===null?0:performance.now()-runStartedAt);const minutes=Math.floor(elapsed/60000);const seconds=(elapsed%60000)/1000;$('runTimer').textContent=`${String(minutes).padStart(2,'0')}:${seconds.toFixed(1).padStart(4,'0')}`;}
function setControls(){$('stepButton').disabled=busy||state?.won;$('autoButton').disabled=Boolean(state?.won);$('resetButton').disabled=busy;$('engineMode').disabled=busy;}
function showToast(message){const el=$('toast');el.textContent=message;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),3500);}

async function saveConfig(event){event.preventDefault();try{const response=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_key:$('apiKeyInput').value,base_url:$('baseUrlInput').value,model:$('modelInput').value,lang:currentLanguage})});const data=await response.json();if(!response.ok)throw new Error(data.error||t('configFailed'));config=data;renderConfig();$('configDialog').close();showToast(t('configApplied'));}catch(error){showToast(error.message);}}
async function resetConfig(){try{const response=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'reset',lang:currentLanguage})});config=await response.json();renderConfig();showToast(t('envRestored'));}catch(error){showToast(error.message);}}
async function changeLanguage(){languagePreference=$('languageSelect').value;localStorage.setItem('jev-language',languagePreference);currentLanguage=resolveLanguage(languagePreference);applyTranslations();renderConfig();await load();}

$('stepButton').onclick=step;$('autoButton').onclick=toggleAuto;$('resetButton').onclick=()=>{stopAuto();resetRunTimer();request('/api/reset');};
$('configButton').onclick=async()=>{await loadConfig();$('configDialog').showModal();};$('closeConfig').onclick=()=>$('configDialog').close();
$('configForm').onsubmit=saveConfig;$('resetConfig').onclick=resetConfig;$('languageSelect').onchange=changeLanguage;
document.addEventListener('keydown',event=>{if(event.target.matches('select,input'))return;const direction={ArrowUp:'up',w:'up',W:'up',ArrowRight:'right',d:'right',D:'right',ArrowDown:'down',s:'down',S:'down',ArrowLeft:'left',a:'left',A:'left'}[event.key];if(!direction||busy||!state)return;event.preventDefault();const action=state.actions.find(item=>item.direction===direction);if(action)move(action.id);});

applyTranslations();
Promise.all([load(),loadConfig()]).catch(error=>showToast(error.message));
