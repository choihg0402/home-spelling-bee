# -*- coding: utf-8 -*-
"""로그인을 메일 링크에서 비밀번호로 바꾼다. 기기마다 비밀번호 한 번만 넣으면 된다."""
import io

P = 'index.template.html'
s = io.open(P, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    assert c == n, (a[:70].replace('\n', '|'), c)
    s = s.replace(a, b)


def span(start, end, new):
    global s
    i = s.index(start)
    j = s.index(end, i) + len(end)
    s = s[:i] + new + s[j:]


# ── 설정: 빌드에 박힌 값을 먼저 쓰고, 없으면 기기에 저장된 값 ──
rep("""function loadSyncCfg(){
  try{ syncCfg=JSON.parse(localStorage.getItem(SYNC_CFG)||'null') }catch(e){ syncCfg=null }
  return syncCfg;
}""",
"""function loadSyncCfg(){
  // 빌드에 박아둔 값이 있으면 그것을 쓴다. 기기마다 붙여넣을 필요가 없다.
  if(typeof SB!=='undefined' && SB.url && SB.key){
    syncCfg={url:SB.url.replace(/\\/+$/,''), key:SB.key, email:SB.email};
    return syncCfg;
  }
  try{ syncCfg=JSON.parse(localStorage.getItem(SYNC_CFG)||'null') }catch(e){ syncCfg=null }
  return syncCfg;
}
function familyEmail(){
  const c=loadSyncCfg();
  return (c && c.email) || (typeof SB!=='undefined' && SB.email) || 'family@spellingbee.home';
}""")

# ── 메일 링크 관련 코드를 비밀번호 로그인으로 교체 ──
span("/* --- 로그인: 비밀번호 없이 메일 링크 --- */",
     "  history.replaceState(null,'',location.pathname+location.search);\n  return true;\n}",
"""/* --- 로그인: 가족 계정 하나에 비밀번호만 --- */
async function signInWithPassword(pw){
  const cfg=loadSyncCfg(); if(!cfg) throw new Error('서버 설정이 없어요');
  const res=await fetch(cfg.url+'/auth/v1/token?grant_type=password', {
    method:'POST',
    headers:{'apikey':cfg.key,'Content-Type':'application/json'},
    body:JSON.stringify({email:familyEmail(), password:pw})
  });
  if(!res.ok){
    let m=''; try{ const j=await res.json(); m=j.error_description||j.msg||j.message||'' }catch(e){}
    if(/invalid/i.test(m)) m='비밀번호가 맞지 않아요.';
    else if(/confirm/i.test(m)) m='계정이 아직 확인되지 않았어요. Supabase 에서 사용자를 만들 때 Auto Confirm 을 켜주세요.';
    throw new Error(m||('로그인하지 못했어요 ('+res.status+')'));
  }
  const j=await res.json();
  setSyncToken({access_token:j.access_token, refresh_token:j.refresh_token,
                expires_at: Math.floor(Date.now()/1000)+(j.expires_in||3600)});
}""")

# ── 화면: 비밀번호 한 칸 ──
span('        <div id="sync-in" class="bk-act">',
     '        <div id="sync-out" class="bk-act" hidden>',
"""        <div id="sync-in" class="bk-act">
          <input id="sync-pw" type="password" autocomplete="current-password"
                 placeholder="가족 비밀번호"
                 onkeydown="if(event.key==='Enter')doSignIn()"
                 style="flex:1;min-width:180px;padding:11px 13px;border-radius:var(--r-m);
                        border:1px solid var(--line);background:var(--paper);color:var(--ink);
                        font:inherit;font-size:15px;min-height:var(--tap)">
          <button class="btn primary" onclick="doSignIn()">로그인</button>
        </div>

        <div id="sync-out" class="bk-act" hidden>""")

# ── 로그인 동작 ──
span("async function doSignIn(){", "  }catch(e){ box.innerHTML='<span class=\"bk-err\">보내지 못했어요 — '+e.message+'</span>' }\n}",
"""async function doSignIn(){
  const el=document.getElementById('sync-pw');
  const pw=el.value;
  if(!pw){ toast('비밀번호를 넣어주세요'); return }
  const box=document.getElementById('sync-state');
  box.innerHTML='<span class="bk-note">로그인 중…</span>';
  try{
    await signInWithPassword(pw);
    el.value='';
    toast('가족 계정에 연결됐어요');
    await renderSync();
    syncNow(true);
  }catch(e){
    box.innerHTML='<span class="bk-err">'+e.message+'</span>';
  }
}""")

# ── 서버 설정 칸은 빌드에 값이 있으면 감춘다 ──
rep("""  const cfgBox=document.getElementById('sync-cfg');
  if(cfgBox){
    document.getElementById('sync-url').value=(cfg&&cfg.url)||'';
    document.getElementById('sync-key').value=(cfg&&cfg.key)||'';
  }""",
"""  const built = typeof SB!=='undefined' && SB.url && SB.key;
  const det=document.getElementById('sync-adv');
  if(det) det.hidden = built;          // 앱에 이미 들어 있으면 설정 칸을 보일 이유가 없다
  const cfgBox=document.getElementById('sync-cfg');
  if(cfgBox && !built){
    document.getElementById('sync-url').value=(cfg&&cfg.url)||'';
    document.getElementById('sync-key').value=(cfg&&cfg.key)||'';
  }""")

rep("""      <details style="margin-top:14px">
        <summary class="sub" style="cursor:pointer">서버 설정</summary>""",
"""      <details style="margin-top:14px" id="sync-adv">
        <summary class="sub" style="cursor:pointer">서버 설정</summary>""")

# ── 안내 문구 ──
rep("""    box.innerHTML='<span class="warn">아직 서버를 연결하지 않았어요.</span>'+
      '<span class="bk-note">연결하기 전에도 앱은 그대로 쓸 수 있어요. 기기끼리 맞추려면 아래 설정이 필요합니다.</span>';""",
"""    box.innerHTML='<span class="warn">아직 서버가 준비되지 않았어요.</span>'+
      '<span class="bk-note">연결하기 전에도 앱은 그대로 쓸 수 있어요.</span>';""")

rep("""    : '<span class="warn">아직 로그인하지 않았어요.</span><span class="bk-note">메일로 받은 링크를 이 기기에서 한 번 열면 됩니다.</span>';""",
"""    : '<span class="warn">이 기기는 아직 연결되지 않았어요.</span>'+
      '<span class="bk-note">가족 비밀번호를 한 번만 넣으면 이 기기가 계속 연결됩니다. 아이는 다시 볼 일이 없어요.</span>';""")

# ── 메일 링크 잔재 제거 ──
span("/* 링크가 엉뚱한 주소(localhost 등)로 열렸을 때", "  renderSync(); setTimeout(()=>syncNow(true),400);\n}", "")
rep("""        <details style="margin-top:10px">
          <summary class="sub" style="cursor:pointer">링크가 다른 주소로 열렸나요?</summary>
          <p class="bk-note" style="margin-top:8px">
            메일 링크를 눌렀는데 <b>연결할 수 없음</b> 같은 화면이 떴다면, 그 화면의
            <b>주소창 주소를 통째로 복사</b>해 아래에 붙여넣으세요. 그것만으로 연결됩니다.
          </p>
          <div class="bk-act" style="margin-top:8px">
            <input id="sync-paste" placeholder="http://localhost:3000/#access_token=..."
                   style="flex:1;min-width:200px;padding:10px 12px;border-radius:var(--r-m);
                          border:1px solid var(--line);background:var(--paper);color:var(--ink);
                          font:inherit;font-size:14px">
            <button class="btn" onclick="finishFromUrl()">연결 마치기</button>
          </div>
        </details>

""", 1)
rep("""addEventListener('load', ()=>{
  if(catchAuthRedirect()){ toast('가족 계정에 연결됐어요'); setTimeout(()=>syncNow(true),400) }
  else setTimeout(()=>autoSync(),800);
}, {once:true});""",
"""addEventListener('load', ()=>setTimeout(()=>autoSync(),800), {once:true});""")

io.open(P, 'w', encoding='utf-8').write(s)
print('비밀번호 로그인으로 교체')
