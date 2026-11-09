import os, secrets, string, json, hashlib
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify, Response, redirect, session
from core import *
from worker import start_background_worker

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-change-me')
init_db(); seed()
if os.getenv('RUN_WORKER_IN_WEB','0') == '1':
    start_background_worker()

CSS = '''
:root{--bg:#070b12;--bg2:#0b1220;--panel:#111b2b;--panel2:#17243a;--panel3:#1d304d;--line:#2c4667;--line2:#3e618d;--text:#f4f8ff;--muted:#9eafc6;--blue:#77b7ff;--cyan:#73e1ff;--green:#72e3ac;--red:#ff7e8b;--yellow:#f6d477;--shadow:0 18px 40px rgba(0,0,0,.35),inset 0 1px rgba(255,255,255,.08)}
*{box-sizing:border-box}html{background:var(--bg)}body{margin:0;background:radial-gradient(circle at 80% -10%,#173254 0,#0b1220 34%,#070b12 72%);background-attachment:fixed;color:var(--text);font:14px Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;min-height:100vh}a{color:inherit;text-decoration:none}button,input,select,textarea{font:inherit}button{cursor:pointer;border:1px solid #d5e8ff;background:linear-gradient(180deg,#f7fbff 0%,#b7d3ef 100%);color:#08111d;border-radius:9px;padding:10px 15px;font-weight:800;box-shadow:0 4px 0 #557da6,0 8px 18px rgba(0,0,0,.25),inset 0 1px #fff;transition:.15s transform,.15s box-shadow}button:hover{transform:translateY(-2px);box-shadow:0 6px 0 #557da6,0 12px 22px rgba(0,0,0,.3),inset 0 1px #fff}button:active{transform:translateY(2px);box-shadow:0 2px 0 #557da6,0 4px 10px rgba(0,0,0,.25)}button.ghost{background:linear-gradient(180deg,#203754,#14243a);color:var(--text);border-color:var(--line2);box-shadow:0 4px 0 #0a1728,0 8px 16px rgba(0,0,0,.22)}button.danger{background:linear-gradient(180deg,#6e2f3d,#421b29);color:#ffe9ed;border-color:#b65b6c;box-shadow:0 4px 0 #2b111a,0 8px 16px rgba(0,0,0,.22)}.top{height:66px;display:flex;align-items:center;gap:24px;padding:0 28px;border-bottom:1px solid var(--line);background:rgba(7,12,21,.88);backdrop-filter:blur(18px);position:sticky;top:0;z-index:5;box-shadow:0 8px 28px rgba(0,0,0,.2)}.brand{font-size:19px;font-weight:950;letter-spacing:.17em;margin-right:auto;text-shadow:0 0 18px rgba(115,225,255,.35)}.top>a:not(.brand){color:var(--muted);font-weight:700}.shell{display:flex;min-height:calc(100vh - 66px)}.side{width:248px;background:linear-gradient(180deg,rgba(13,25,43,.98),rgba(8,15,27,.96));border-right:1px solid var(--line);padding:22px 15px;flex:none;box-shadow:14px 0 35px rgba(0,0,0,.18)}.side:before{content:'CONTROL CENTER';display:block;font-size:10px;letter-spacing:.18em;color:#607997;padding:0 14px 14px}.side a{display:flex;align-items:center;gap:10px;padding:13px 14px;border-radius:10px;color:var(--muted);margin:5px 0;font-weight:700;border:1px solid transparent;transition:.15s}.side a:before{content:'◆';font-size:8px;color:#52779e}.side a:hover,.side a.active{background:linear-gradient(135deg,#203b5e,#14263f);color:var(--text);border-color:#3d628d;box-shadow:var(--shadow);transform:translateX(2px)}.main{padding:32px;max-width:1600px;width:100%;margin:auto}.pagehead{display:flex;justify-content:space-between;gap:20px;align-items:center;margin-bottom:24px}.pagehead h1{margin:0;font-size:30px;letter-spacing:-.02em}.pagehead h1:after{content:'';display:block;width:52px;height:3px;margin-top:10px;border-radius:3px;background:linear-gradient(90deg,var(--cyan),transparent)}.muted{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.card{background:linear-gradient(145deg,rgba(25,43,68,.96),rgba(13,24,40,.96));border:1px solid var(--line);border-radius:15px;padding:20px;box-shadow:var(--shadow);position:relative;overflow:hidden}.card:before{content:'';position:absolute;inset:0 0 auto;height:1px;background:linear-gradient(90deg,transparent,#8dc8ff,transparent);opacity:.55}.card:hover{border-color:var(--line2);box-shadow:0 22px 48px rgba(0,0,0,.42),inset 0 1px rgba(255,255,255,.1);transform:translateY(-1px)}.stat{min-height:142px}.stat small{display:block;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:.08em}.stat strong{display:block;font-size:34px;margin:16px 0 8px;background:linear-gradient(90deg,#fff,var(--cyan));-webkit-background-clip:text;background-clip:text;color:transparent}.stat b{color:var(--green);font-size:12px}.toolbar,.formrow,.actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:16px}.input,.select,.textarea{background:rgba(5,12,22,.8);border:1px solid var(--line2);color:var(--text);border-radius:9px;padding:11px 13px;outline:none;box-shadow:inset 0 2px 8px rgba(0,0,0,.25)}.input:focus,.select:focus,.textarea:focus{border-color:var(--cyan);box-shadow:0 0 0 3px rgba(115,225,255,.12),inset 0 2px 8px rgba(0,0,0,.25)}.input{min-width:210px}.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:13px;box-shadow:var(--shadow)}.table{width:100%;border-collapse:collapse;min-width:900px}.table th,.table td{text-align:left;padding:14px 15px;border-bottom:1px solid rgba(62,97,141,.45);white-space:nowrap}.table th{background:linear-gradient(180deg,#1b304d,#14243a);color:#b8cbe1;font-size:11px;letter-spacing:.08em;text-transform:uppercase}.table tr:hover td{background:rgba(60,100,148,.12)}.table tr:last-child td{border-bottom:0}.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:#bfe5ff}.badge{display:inline-block;border-radius:999px;padding:5px 10px;font-size:11px;font-weight:800;border:1px solid}.ok{background:rgba(29,105,71,.32);color:var(--green);border-color:#3b986e}.bad{background:rgba(121,35,49,.32);color:var(--red);border-color:#ad5265}.warn{background:rgba(128,97,22,.3);color:var(--yellow);border-color:#aa8b39}.formcard{max-width:760px}.field{display:grid;gap:8px;margin-bottom:17px}.field label{color:#c3d3e7;font-size:13px;font-weight:700}.help{font-size:12px;color:var(--muted)}.alert{padding:13px;border:1px solid #a24f60;background:rgba(82,24,35,.7);color:#ffd8df;border-radius:9px;margin-bottom:16px}.keybox{font-size:23px;padding:16px;background:rgba(4,10,18,.75);border:1px dashed #6c9cca;border-radius:10px;box-shadow:inset 0 2px 12px rgba(0,0,0,.25)}.health{width:10px;height:10px;border-radius:50%;display:inline-block;background:var(--green);margin-right:8px;box-shadow:0 0 12px currentColor}.health.red{background:var(--red)}.health.yellow{background:var(--yellow)}.public{max-width:920px;margin:auto;padding:65px 22px}.public h1{font-size:48px}.jsonhint{background:linear-gradient(145deg,#142741,#0e192a);border:1px solid var(--line2);padding:20px;border-radius:12px;white-space:pre-wrap;box-shadow:var(--shadow)}.empty{text-align:center;padding:42px;color:var(--muted)}.mobilebar{display:none}
@media(max-width:900px){.side{width:210px}.grid{grid-template-columns:repeat(2,1fr)}.main{padding:24px}.top{padding:0 18px}}
@media(max-width:640px){.top{height:60px}.top>a:not(.brand){display:none}.brand{font-size:16px}.shell{min-height:calc(100vh - 60px)}.side{display:none}.main{padding:18px 14px 88px}.pagehead{align-items:flex-start;flex-direction:column}.pagehead h1{font-size:25px}.grid,.grid3{grid-template-columns:1fr}.card{padding:16px}.mobilebar{display:flex;position:fixed;bottom:0;left:0;right:0;height:68px;z-index:8;background:rgba(8,15,27,.96);border-top:1px solid var(--line);backdrop-filter:blur(18px);justify-content:space-around;align-items:center;box-shadow:0 -12px 30px rgba(0,0,0,.35)}.mobilebar a{font-size:11px;color:var(--muted);text-align:center}.mobilebar a b{display:block;color:var(--cyan);font-size:18px;margin-bottom:3px}.formrow,.toolbar{align-items:stretch}.formrow>* ,.toolbar>*{width:100%}.input,.select{min-width:0}.table{min-width:820px}.keybox{font-size:17px;overflow:auto}.actions{align-items:stretch}.actions button,.actions form{width:100%}.actions form button{width:100%}}
'''

def page(title, body, admin=False, active=''):
    nav = ''.join(f'<a class="{"active" if active==key else ""}" href="{href}">{label}</a>' for key,href,label in [
        ('dash','/admin','Dashboard'),('keys','/admin/keys','Quản lý key'),('codes','/admin/codes','Mã kích hoạt'),('games','/admin/games','Game & bàn'),('monitor','/admin/monitor','Theo dõi engine'),('logs','/admin/logs','Nhật ký'),('support','/admin/support','Hỗ trợ')])
    if admin:
        return f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body><header class="top"><a class="brand" href="/admin">PAWNOVA ADMIN</a><a href="/">Trang public</a><form method="post" action="/admin/logout"><button class="ghost">Đăng xuất</button></form></header><div class="shell"><aside class="side">{nav}</aside><main class="main">{body}</main></div><nav class="mobilebar"><a href="/admin"><b>⌂</b>Tổng quan</a><a href="/admin/keys"><b>KEY</b>Key</a><a href="/admin/monitor"><b>◉</b>Monitor</a><a href="/admin/logs"><b>≡</b>Log</a></nav></body></html>'''
    return f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body><header class="top"><a class="brand" href="/">PAWNOVA</a><a href="/pricing">Bảng giá</a><a href="/support">Hỗ trợ</a></header><main class="public">{body}</main></body></html>'''

def admin_auth():
    if session.get('admin_user') == os.getenv('ADMIN_USER','admin'):
        return None
    a = request.authorization
    if a and a.username == os.getenv('ADMIN_USER','admin') and a.password == os.getenv('ADMIN_PASS','change-me'):
        session['admin_user'] = a.username
        return None
    if request.path.startswith('/admin/') or request.path == '/admin':
        return redirect('/admin/login?next='+request.path)
    return Response('Yêu cầu đăng nhập admin', 401, {'WWW-Authenticate':'Basic realm="PAWNOVA Admin"'})

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    error=''
    if request.method == 'POST':
        if request.form.get('username') == os.getenv('ADMIN_USER','admin') and request.form.get('password') == os.getenv('ADMIN_PASS','change-me'):
            session['admin_user'] = request.form['username']
            return redirect(request.args.get('next') or '/admin')
        error='Sai tài khoản hoặc mật khẩu admin'
    return page('Đăng nhập admin', f'''<div style="max-width:420px;margin:70px auto"><div class="card"><h1>Đăng nhập admin</h1>{f'<div class="alert">{error}</div>' if error else ''}<form method="post" class="field"><label>Tài khoản</label><input class="input" name="username" autocomplete="username" required><label>Mật khẩu</label><input class="input" type="password" name="password" autocomplete="current-password" required><button>Đăng nhập</button></form></div></div>''')

@app.post('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/admin/login')

def audit(action, target='', detail=''):
    with db() as c:
        c.execute('INSERT INTO admin_actions(admin_user,action,target,detail_json,ip,user_agent) VALUES(?,?,?,?,?,?)', ('admin',action,target,detail,request.remote_addr,request.user_agent.string))

def key_value(prefix='paw'):
    while True:
        value = prefix + ''.join(secrets.choice(string.digits) for _ in range(12))
        if not row('SELECT key FROM api_keys WHERE key=?',(value,)): return value

def duration_hours(value):
    return {'12h':12, '1d':24, '5d':120, '15d':360, '30d':720}.get(value,24)

def expiry_for(duration):
    return (datetime.now(timezone.utc)+timedelta(hours=duration_hours(duration))).replace(microsecond=0).isoformat().replace('+00:00','Z')

def scope_options(selected='ALL'):
    vals=['ALL','68gb','b52','sunwin','max789','lc79','betvip']+[x['code'] for x in rows('SELECT code FROM tables_ ORDER BY sort_order')]
    return ''.join(f'<option value="{x}" {"selected" if x==selected else ""}>{x}</option>' for x in vals)

def key_status(k):
    if not k['is_active']: return '<span class="badge bad">Đã khóa</span>'
    if k['expires_at'] and k['expires_at'] <= now_iso(): return '<span class="badge bad">Hết hạn</span>'
    return '<span class="badge ok">Đang hoạt động</span>'

def table_for(game, typ): return row('SELECT t.*,g.name game_name FROM tables_ t JOIN games g ON g.code=t.game_code WHERE t.code=?',(f'{game}_{typ}',))
def prediction_view(r): return {'phien':r['session_id'],'dudoan':r['prediction'],'ketqua':r['actual'] or 'chuacoketqua','trangthai':'win✅' if r['result']=='win' else 'lose❌' if r['result']=='lose' else ''}

def request_device():
    did=request.headers.get('X-Device-Id') or hashlib.sha256(f'{request.remote_addr or "unknown"}|{request.user_agent.string}'.encode()).hexdigest()[:32]
    return {'device_id':did,'device_short':did[:12],'ip':request.remote_addr,'user_agent':request.user_agent.string,'api_header':'X-Device-Id: '+did}

def key_permissions(k):
    tables=rows('SELECT code,game_code,table_type FROM tables_ ORDER BY sort_order')
    allowed=[dict(t) for t in tables if Auth.scope(k['scope'],t['code'])]
    return {'scope':k['scope'],'total_tables':len(allowed),'tables':[t['code'] for t in allowed],'games':sorted(set(t['game_code'] for t in allowed)),'items':[{'table_code':t['code'],'game':t['game_code'],'table':t['table_type'],'prediction':f'/api/{t["game_code"]}/{t["table_type"]}/ma?key={k["key"]}','history':f'/api/{t["game_code"]}/{t["table_type"]}/history?key={k["key"]}'} for t in allowed]}

@app.after_request
def cors(resp):
    if request.path.startswith('/api/') or request.path.startswith('/tx/api/'):
        resp.headers.update({'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET,POST,OPTIONS','Access-Control-Allow-Headers':'Content-Type,X-API-Key,X-Device-Id'})
    return resp

@app.get('/')
def home():
    return page('PAWNOVA','<h1>PAWNOVA</h1><p class="muted">API dự đoán Tài Xỉu cho 6 game · 11 bàn.</p><div class="jsonhint">User không cần vào web. Gọi trực tiếp:<br><br>GET /tx/api/makey/&lt;KEY&gt;<br><br>Ví dụ: /tx/api/makey/paw123456789012</div>')

@app.get('/pricing')
def pricing(): return page('Bảng giá','<h1>Bảng giá</h1><div class="grid3"><div class="card">Từng bàn<strong>50.000đ/tuần</strong></div><div class="card">Gói game<strong>80.000đ/tuần</strong></div><div class="card">Tất cả 11 bàn<strong>350.000đ/tuần</strong></div></div>')
@app.get('/support')
def support(): return page('Hỗ trợ','<h1>Hỗ trợ</h1><div class="card"><h3>Cách dùng key</h3><p>Gọi GET /tx/api/makey/&lt;KEY&gt; để nhận JSON thông tin key và bàn được cấp.</p><p>API dự đoán dùng X-API-Key hoặc tham số key.</p></div>')

@app.get('/tx/api/makey/<key>')
def makey(key):
    k=row('SELECT * FROM api_keys WHERE key=?',(key,))
    if not k: return jsonify(ok=False,error='key_not_found',message='Mã key không tồn tại'),404
    active=bool(k['is_active']) and (not k['expires_at'] or k['expires_at']>now_iso())
    base=request.url_root.rstrip('/')
    permissions=key_permissions(k)
    device=request_device()
    current=row("SELECT device_id,ip,user_agent,first_seen,last_seen,released_at FROM api_key_devices WHERE key=? AND device_id=? ORDER BY id DESC LIMIT 1",(key,device['device_id']))
    device['registered']=bool(current);device['first_seen']=current['first_seen'] if current else None;device['last_seen']=current['last_seen'] if current else None;device['locked']=bool(current and not current['released_at'])
    return jsonify({'ok':active,'key':k['key'],'status':'active' if active else 'expired_or_revoked','expires_at':k['expires_at'],'note':k['note'],'permissions':permissions,'device':device,'links':{'key_info':f'{base}/tx/api/makey/{key}','activate':f'{base}/tx/api/makey/{key}/activate','admin_api':f'{base}/api/<game>/<table>/chitiet?key={key}'},'request':{'method':'GET','header':'X-API-Key: '+key,'device_header':'X-Device-Id: '+device['device_id']}})

@app.post('/tx/api/makey/<key>/activate')
def activate_key(key):
    k=row('SELECT * FROM api_keys WHERE key=?',(key,));data=request.get_json(silent=True) or request.form;code=str(data.get('code','')).strip().upper();c=row('SELECT * FROM activation_codes WHERE code=?',(code,)) if code else None
    if not k:return jsonify(ok=False,error='key_not_found',message='Mã key không tồn tại'),404
    reason='ok'
    if not c:reason='invalid'
    elif c['revoked']:reason='revoked'
    elif c['expires_at'] and c['expires_at']<=now_iso():reason='expired'
    elif c['max_uses']!=-1 and c['used_count']>=c['max_uses']:reason='exhausted'
    if reason!='ok':
        with db() as x:x.execute('INSERT INTO activation_log(key,code,success,ip,user_agent,reason) VALUES(?,?,?,?,?,?)',(key,code,0,request.remote_addr,request.user_agent.string,reason))
        return jsonify(ok=False,error='activation_failed',reason=reason,message='Mã kích hoạt không hợp lệ'),400
    exp=(datetime.now(timezone.utc)+timedelta(days=c['days'])).replace(microsecond=0).isoformat().replace('+00:00','Z')
    with db() as x:
        x.execute('UPDATE activation_codes SET used_count=used_count+1 WHERE code=?',(code,));x.execute('UPDATE api_keys SET scope=?,expires_at=?,is_active=1 WHERE key=?',(c['scope'],exp,key));x.execute('INSERT INTO activation_log(key,code,success,ip,user_agent,reason) VALUES(?,?,?,?,?,?)',(key,code,1,request.remote_addr,request.user_agent.string,'ok'))
    return jsonify(ok=True,message='Kích hoạt key thành công',key=key,scope=c['scope'],expires_at=exp,info_url=request.url_root.rstrip('/')+'/tx/api/makey/'+key)

@app.get('/api/<game>/<typ>/ma')
def api_prediction(game,typ):
    t=table_for(game,typ)
    if not t:return jsonify(error='not_found',message='Bàn không tồn tại'),404
    k,e=Auth.key(t['code'])
    if e:return e
    r=row('SELECT session_id,prediction,actual,result FROM predictions WHERE table_code=? ORDER BY session_id DESC LIMIT 1',(t['code'],))
    return jsonify({'admin':'P A W','telegram':'@K0ZT1',**(prediction_view(r) if r else {'phien':0,'dudoan':None,'ketqua':'chuacoketqua','trangthai':''})})

@app.get('/api/<game>/<typ>/history')
def api_history(game,typ):
    t=table_for(game,typ)
    if not t:return jsonify(error='not_found',message='Bàn không tồn tại'),404
    k,e=Auth.key(t['code'])
    if e:return e
    rs=rows('SELECT session_id,prediction,actual,result FROM predictions WHERE table_code=? AND actual IS NOT NULL ORDER BY session_id DESC LIMIT 50',(t['code'],))
    return jsonify(count=len(rs),items=[prediction_view(x) for x in rs])

@app.get('/api/<game>/<typ>/chitiet')
def api_detail(game,typ):
    t=table_for(game,typ)
    if not t:return jsonify(error='not_found',message='Bàn không tồn tại'),404
    k,e=Auth.key(t['code'],True)
    if e:return e
    rs=rows('SELECT result FROM predictions WHERE table_code=? AND actual IS NOT NULL ORDER BY session_id DESC LIMIT 100',(t['code'],));wins=sum(x['result']=='win' for x in rs)
    return jsonify(table_code=t['code'],game=game,game_name=t['game_name'],table=typ,stats={'predictions_total':len(rs),'wins':wins,'losses':len(rs)-wins,'accuracy_100':wins/max(1,len(rs))})

@app.get('/admin')
def admin_dashboard():
    if (e:=admin_auth()): return e
    keys=rows('SELECT * FROM api_keys');codes=rows('SELECT * FROM activation_codes');pred=rows('SELECT result FROM predictions WHERE actual IS NOT NULL')
    wins=sum(x['result']=='win' for x in pred)
    body=f'''<div class="pagehead"><h1>Dashboard</h1><span class="muted">Quản trị PAWNOVA</span></div><div class="grid"><div class="card stat"><small>Tổng key</small><strong>{len(keys)}</strong><b>Quản lý khách hàng</b></div><div class="card stat"><small>Key hoạt động</small><strong>{sum(1 for k in keys if k['is_active'])}</strong><b>Đang dùng</b></div><div class="card stat"><small>Mã kích hoạt</small><strong>{len(codes)}</strong><b>Tạo mã mới</b></div><div class="card stat"><small>Accuracy</small><strong>{wins/max(1,len(pred)):.1%}</strong><b>{len(pred)} kết quả</b></div></div><br><div class="grid3"><div class="card"><h3>Thao tác nhanh</h3><p><a href="/admin/keys">Tạo và quản lý key →</a></p><p><a href="/admin/monitor">Theo dõi 11 bàn →</a></p><p><a href="/admin/support">Trung tâm hỗ trợ →</a></p></div><div class="card"><h3>Thời hạn key</h3><p>12 giờ · 1 ngày · 5 ngày</p><p>15 ngày · 30 ngày</p></div><div class="card"><h3>Phạm vi cấp quyền</h3><p>Từng bàn · từng game · ALL</p><p>Key mẫu: <span class="mono">paw12345</span></p></div></div>'''
    return page('Admin dashboard',body,True,'dash')

@app.get('/admin/keys')
def admin_keys():
    if (e:=admin_auth()): return e
    q=request.args.get('q','').strip(); ks=rows('SELECT * FROM api_keys WHERE key LIKE ? OR scope LIKE ? ORDER BY created_at DESC',('%'+q+'%','%'+q+'%'))
    trs=''.join(f'''<tr><td><a class="mono" href="/admin/keys/{k['key']}">{k['key']}</a></td><td>{k['scope']}</td><td>{k['expires_at'] or '—'}</td><td>{key_status(k)}</td><td><div class="actions"><a href="/admin/keys/{k['key']}">Chi tiết</a><form method="post" action="/admin/keys/{k['key']}/revoke"><button class="danger">Thu hồi</button></form></div></td></tr>''' for k in ks)
    body=f'''<div class="pagehead"><h1>Quản lý key</h1><a href="/admin/keys/create"><button>Tạo key mới</button></a></div><form class="toolbar"><input class="input" name="q" value="{q}" placeholder="Tìm key hoặc scope"><button class="ghost">Tìm</button></form><div class="tablewrap"><table class="table"><tr><th>Key</th><th>Phạm vi</th><th>Hết hạn</th><th>Trạng thái</th><th>Thao tác</th></tr>{trs or '<tr><td colspan="5" class="empty">Chưa có key</td></tr>'}</table></div>'''
    return page('Quản lý key',body,True,'keys')

@app.route('/admin/keys/create',methods=['GET','POST'])
def admin_create_key():
    if (e:=admin_auth()): return e
    if request.method=='POST':
        key=key_value();scope=request.form.get('scope','ALL');duration=request.form.get('duration','1d');note=request.form.get('note','').strip();exp=expiry_for(duration)
        with db() as c:c.execute('INSERT INTO api_keys(key,scope,note,is_active,expires_at) VALUES(?,?,?,?,?)',(key,scope,note,1,exp))
        audit('create_key',key,json.dumps({'scope':scope,'duration':duration}));return redirect('/admin/keys/'+key)
    body=f'''<div class="pagehead"><h1>Tạo key cho khách</h1><a href="/admin/keys">← Danh sách key</a></div><form class="card formcard" method="post"><div class="field"><label>Thời hạn</label><select class="select" name="duration"><option value="12h">12 giờ</option><option value="1d" selected>1 ngày</option><option value="5d">5 ngày</option><option value="15d">15 ngày</option><option value="30d">30 ngày</option></select></div><div class="field"><label>Phạm vi dùng key</label><select class="select" name="scope">{scope_options()}</select><span class="help">Chọn ALL, game bundle hoặc từng bàn.</span></div><div class="field"><label>Ghi chú khách hàng</label><input class="input" name="note" placeholder="Tên khách / số điện thoại / ghi chú"></div><button>Tạo key paw + số random</button></form>'''
    return page('Tạo key',body,True,'keys')

@app.get('/admin/keys/<key>')
def admin_key_detail(key):
    if (e:=admin_auth()): return e
    k=row('SELECT * FROM api_keys WHERE key=?',(key,))
    if not k:return page('Không tìm thấy','<div class="alert">Key không tồn tại.</div>',True,'keys'),404
    devices=rows('SELECT * FROM api_key_devices WHERE key=? ORDER BY id DESC LIMIT 20',(key,));dev=''.join(f'<tr><td class="mono">{d["device_id"][:12]}</td><td>{d["ip"] or "—"}</td><td>{d["user_agent"] or "—"}</td><td>{d["last_seen"]}</td><td>{d["released_at"] or "Đang hoạt động"}</td></tr>' for d in devices)
    base=request.url_root.rstrip('/')
    allowed=[t for t in rows('SELECT code,game_code,table_type FROM tables_ ORDER BY sort_order') if Auth.scope(k['scope'],t['code'])]
    links='\n'.join(f'- {t["game_code"].upper()} {t["table_type"].upper()}: {base}/api/{t["game_code"]}/{t["table_type"]}/ma?key={key}\n  Lịch sử: {base}/api/{t["game_code"]}/{t["table_type"]}/history?key={key}' for t in allowed)
    share=f'''PAWNOVA - THÔNG TIN API KEY\n\nKey: {key}\nThời hạn: {k['expires_at'] or 'Chưa kích hoạt'}\nPhạm vi: {k['scope']}\n\nLink kiểm tra key:\n{base}/tx/api/makey/{key}\n\nLink API sử dụng:\n{links}\n\nGửi request bằng trình duyệt hoặc dùng tham số ?key={key}.'''
    body=f'''<div class="pagehead"><h1>Chi tiết key</h1><a href="/admin/keys">← Danh sách</a></div><div class="card"><div class="keybox mono">{k['key']}</div><p>Scope: <b>{k['scope']}</b> · Hết hạn: <b>{k['expires_at'] or '—'}</b> · {key_status(k)}</p><p class="muted">Ghi chú: {k['note'] or '—'} · Tạo lúc: {k['created_at']}</p><div class="actions"><form method="post" action="/admin/keys/{key}/unlock"><button>Mở khóa thiết bị</button></form><form method="post" action="/admin/keys/{key}/revoke"><button class="danger">Thu hồi key</button></form></div></div><br><div class="card"><div class="pagehead"><h2>Nội dung gửi khách</h2><button type="button" onclick="navigator.clipboard.writeText(document.getElementById('share-message').value);this.textContent='Đã sao chép'">Sao chép toàn bộ</button></div><textarea id="share-message" class="textarea" rows="16" style="width:100%;resize:vertical">{share}</textarea><p class="help">Admin chỉ cần bấm “Sao chép toàn bộ” rồi gửi cho khách.</p></div><br><div class="card"><h2>Thiết bị và lịch sử dùng key</h2><div class="tablewrap"><table class="table"><tr><th>Device</th><th>IP</th><th>Trình duyệt</th><th>Lần cuối</th><th>Trạng thái</th></tr>{dev or '<tr><td colspan="5" class="empty">Chưa có thiết bị</td></tr>'}</table></div></div>'''
    return page('Chi tiết key',body,True,'keys')

@app.post('/admin/keys/<key>/unlock')
def unlock_key(key):
    if (e:=admin_auth()): return e
    with db() as c:c.execute("UPDATE api_key_devices SET released_at=?,released_reason='admin' WHERE key=? AND released_at IS NULL",(now_iso(),key))
    audit('unlock_device',key);return redirect('/admin/keys/'+key)
@app.post('/admin/keys/<key>/revoke')
def revoke_key(key):
    if (e:=admin_auth()): return e
    with db() as c:c.execute('UPDATE api_keys SET is_active=0 WHERE key=?',(key,))
    audit('revoke_key',key);return redirect('/admin/keys')

@app.route('/admin/codes',methods=['GET','POST'])
def admin_codes():
    if (e:=admin_auth()): return e
    if request.method=='POST':
        alphabet='23456789ABCDEFGHJKMNPQRSTUVWXYZ';code='TX'+''.join(secrets.choice(alphabet) for _ in range(10));scope=request.form.get('scope','ALL');days=int(request.form.get('days','7'));max_uses=int(request.form.get('max_uses','-1'))
        with db() as c:c.execute('INSERT INTO activation_codes(code,scope,days,max_uses,created_by) VALUES(?,?,?,?,?)',(code,scope,days,max_uses,'admin'))
        audit('create_code',code);return redirect('/admin/codes')
    cs=rows('SELECT * FROM activation_codes ORDER BY created_at DESC');trs=''.join(f'<tr><td class="mono">{c["code"]}</td><td>{c["scope"]}</td><td>{c["days"]} ngày</td><td>{c["used_count"]}/{c["max_uses"]}</td><td>{"Đã thu hồi" if c["revoked"] else "Hoạt động"}</td></tr>' for c in cs)
    body=f'''<div class="pagehead"><h1>Mã kích hoạt</h1></div><form class="card formrow" method="post"><select class="select" name="scope">{scope_options()}</select><input class="input" name="days" type="number" min="1" max="365" value="7" placeholder="Số ngày"><input class="input" name="max_uses" type="number" value="-1" placeholder="-1 = không giới hạn"><button>Tạo mã</button></form><div class="tablewrap"><table class="table"><tr><th>Mã</th><th>Scope</th><th>Thời hạn</th><th>Đã dùng</th><th>Trạng thái</th></tr>{trs or '<tr><td colspan="5" class="empty">Chưa có mã</td></tr>'}</table></div>'''
    return page('Mã kích hoạt',body,True,'codes')

@app.get('/admin/games')
def admin_games():
    if (e:=admin_auth()): return e
    gs=rows('SELECT * FROM games ORDER BY sort_order');ts=rows('SELECT * FROM tables_ ORDER BY sort_order');cards=''.join(f'<div class="card"><h2>{g["name"]}</h2>'+''.join(f'<div class="row"><span><span class="health"></span>{t["code"]}</span><span>{"Đang bật" if t["is_active"] else "Tạm dừng"}</span></div>' for t in ts if t['game_code']==g['code'])+'</div>' for g in gs)
    return page('Game và bàn','<div class="pagehead"><h1>Game và 11 bàn</h1></div><div class="grid3">'+cards+'</div>',True,'games')

@app.get('/admin/monitor')
def admin_monitor():
    if (e:=admin_auth()): return e
    ts=rows('SELECT t.*,g.name game_name FROM tables_ t JOIN games g ON g.code=t.game_code ORDER BY t.sort_order');cards=''
    for t in ts:
        p=rows("SELECT result FROM predictions WHERE table_code=? AND actual IS NOT NULL ORDER BY session_id DESC LIMIT 100",(t['code'],));w=sum(x['result']=='win' for x in p);acc=w/max(1,len(p));cards+=f'<div class="card"><h3><span class="health"></span>{t["game_name"]} · {t["table_type"].upper()}</h3><p class="muted">{t["code"]}</p><strong>{acc:.1%}</strong><p>{len(p)} kết quả · {w} thắng · {len(p)-w} thua</p></div>'
    return page('Theo dõi engine','<div class="pagehead"><h1>Theo dõi engine</h1><span class="muted">11 bàn</span></div><div class="grid3">'+cards+'</div>',True,'monitor')

@app.get('/admin/logs')
def admin_logs():
    if (e:=admin_auth()): return e
    logs=rows('SELECT * FROM admin_actions ORDER BY id DESC LIMIT 200');trs=''.join(f'<tr><td>{x["created_at"]}</td><td>{x["admin_user"]}</td><td>{x["action"]}</td><td>{x["target"]}</td><td>{x["detail_json"] or "—"}</td></tr>' for x in logs)
    return page('Nhật ký thao tác','<div class="pagehead"><h1>Nhật ký thao tác</h1></div><div class="tablewrap"><table class="table"><tr><th>Thời gian</th><th>Admin</th><th>Thao tác</th><th>Đối tượng</th><th>Chi tiết</th></tr>'+trs+'</table></div>',True,'logs')

@app.get('/admin/support')
def admin_support():
    if (e:=admin_auth()): return e
    return page('Hỗ trợ','<div class="pagehead"><h1>Trung tâm hỗ trợ</h1></div><div class="grid3"><div class="card"><h3>Key mẫu</h3><p class="mono">paw12345</p><p class="muted">Key thật do admin tạo sẽ có 12 số random.</p></div><div class="card"><h3>Endpoint người dùng</h3><p class="mono">/tx/api/makey/&lt;key&gt;</p><p>Trả JSON, không cần giao diện user.</p></div><div class="card"><h3>Thời hạn</h3><p>12h · 1d · 5d · 15d · 30d</p></div></div>',True,'support')

@app.route('/api/<path:x>',methods=['OPTIONS'])
def options(x): return '',204
@app.errorhandler(404)
def missing(e):
    if request.path.startswith('/api/') or request.path.startswith('/tx/api/'):
        return jsonify(ok=False,error='not_found',message='Không tìm thấy endpoint'),404
    return page('404','<h1>Không tìm thấy trang</h1>'),404
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT','5000')))
