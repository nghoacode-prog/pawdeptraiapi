import os, secrets, string, json
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify, Response, redirect
from core import *

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-change-me')
init_db(); seed()

CSS = '''
:root{--bg:#090a0d;--panel:#12151b;--panel2:#181c24;--line:#29303b;--text:#f5f7fa;--muted:#8e98a8;--blue:#8ab4ff;--green:#7ee2a8;--red:#ff8585;--yellow:#f1ca76}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px Inter,system-ui,-apple-system,Segoe UI,sans-serif}a{color:inherit;text-decoration:none}button,input,select,textarea{font:inherit}button{cursor:pointer;border:1px solid #526071;background:#e9eef5;color:#111;border-radius:8px;padding:10px 14px;font-weight:700}button.ghost{background:transparent;color:var(--text);border-color:var(--line)}button.danger{background:#4a1e26;color:#ffd8d8;border-color:#7d3540}.top{height:62px;display:flex;align-items:center;gap:22px;padding:0 24px;border-bottom:1px solid var(--line);background:#0d1015;position:sticky;top:0;z-index:5}.brand{font-size:18px;font-weight:900;letter-spacing:.15em;margin-right:auto}.top a{color:var(--muted)}.shell{display:flex;min-height:calc(100vh - 62px)}.side{width:235px;background:#0d1015;border-right:1px solid var(--line);padding:20px 14px;flex:none}.side a{display:block;padding:12px 14px;border-radius:8px;color:var(--muted);margin-bottom:4px}.side a:hover,.side a.active{background:var(--panel2);color:var(--text)}.main{padding:28px;max-width:1500px;width:100%;margin:auto}.pagehead{display:flex;justify-content:space-between;gap:20px;align-items:center;margin-bottom:22px}.pagehead h1{margin:0;font-size:28px}.muted{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:15px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:15px}.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px}.stat small{display:block;color:var(--muted);margin-bottom:10px}.stat strong{display:block;font-size:30px}.stat b{color:var(--green);font-size:12px}.toolbar,.formrow{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:16px}.input,.select,.textarea{background:var(--panel2);border:1px solid var(--line);color:var(--text);border-radius:8px;padding:10px 12px}.input{min-width:190px}.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:12px}.table{width:100%;border-collapse:collapse;min-width:850px}.table th,.table td{text-align:left;padding:13px 14px;border-bottom:1px solid var(--line);white-space:nowrap}.table th{background:var(--panel2);color:var(--muted);font-size:12px}.table tr:last-child td{border-bottom:0}.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}.badge{display:inline-block;border-radius:999px;padding:4px 9px;font-size:12px}.ok{background:#173b2b;color:var(--green)}.bad{background:#482027;color:var(--red)}.warn{background:#4a3a19;color:var(--yellow)}.actions{display:flex;gap:7px}.actions form{display:inline}.formcard{max-width:720px}.field{display:grid;gap:7px;margin-bottom:14px}.field label{color:var(--muted);font-size:13px}.help{font-size:12px;color:var(--muted)}.alert{padding:12px;border:1px solid #7d3540;background:#321a20;color:#ffd8d8;border-radius:8px;margin-bottom:16px}.keybox{font-size:22px;padding:15px;background:#0a0d12;border:1px dashed #59687b;border-radius:8px}.health{width:9px;height:9px;border-radius:50%;display:inline-block;background:var(--green);margin-right:7px}.health.red{background:var(--red)}.health.yellow{background:var(--yellow)}.public{max-width:900px;margin:auto;padding:50px 22px}.public h1{font-size:42px}.jsonhint{background:#10141a;border:1px solid var(--line);padding:16px;border-radius:9px;white-space:pre-wrap}.empty{text-align:center;padding:38px;color:var(--muted)}@media(max-width:800px){.side{width:62px;padding:12px 7px}.side a{font-size:0;text-align:center}.side a:before{content:'•';font-size:20px}.main{padding:18px}.grid,.grid3{grid-template-columns:1fr 1fr}.top{padding:0 14px}.top a{display:none}.brand{margin:0}.pagehead{align-items:flex-start;flex-direction:column}}@media(max-width:520px){.grid,.grid3{grid-template-columns:1fr}.table{min-width:760px}}
'''

def page(title, body, admin=False, active=''):
    nav = ''.join(f'<a class="{"active" if active==key else ""}" href="{href}">{label}</a>' for key,href,label in [
        ('dash','/admin','Dashboard'),('keys','/admin/keys','Quản lý key'),('codes','/admin/codes','Mã kích hoạt'),('games','/admin/games','Game & bàn'),('monitor','/admin/monitor','Theo dõi engine'),('logs','/admin/logs','Nhật ký'),('support','/admin/support','Hỗ trợ')])
    if admin:
        return f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body><header class="top"><a class="brand" href="/admin">PAWNOVA ADMIN</a><a href="/">Trang public</a></header><div class="shell"><aside class="side">{nav}</aside><main class="main">{body}</main></div></body></html>'''
    return f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body><header class="top"><a class="brand" href="/">PAWNOVA</a><a href="/pricing">Bảng giá</a><a href="/support">Hỗ trợ</a></header><main class="public">{body}</main></body></html>'''

def admin_auth():
    a = request.authorization
    if not a or a.username != os.getenv('ADMIN_USER','admin') or a.password != os.getenv('ADMIN_PASS','change-me'):
        return Response('Yêu cầu đăng nhập admin', 401, {'WWW-Authenticate':'Basic realm="PAWNOVA Admin"'})

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
    allowed=[t['code'] for t in rows('SELECT code FROM tables_ ORDER BY sort_order') if Auth.scope(k['scope'],t['code'])]
    return jsonify({'ok':active,'key':k['key'],'scope':k['scope'],'status':'active' if active else 'expired_or_revoked','expires_at':k['expires_at'],'tables':allowed,'api':{'prediction':'/api/<game>/<table>/ma?key='+k['key'],'history':'/api/<game>/<table>/history?key='+k['key']}})

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
    body=f'''<div class="pagehead"><h1>Chi tiết key</h1><a href="/admin/keys">← Danh sách</a></div><div class="card"><div class="keybox mono">{k['key']}</div><p>Scope: <b>{k['scope']}</b> · Hết hạn: <b>{k['expires_at'] or '—'}</b> · {key_status(k)}</p><p class="muted">Ghi chú: {k['note'] or '—'} · Tạo lúc: {k['created_at']}</p><div class="actions"><form method="post" action="/admin/keys/{key}/unlock"><button>Mở khóa thiết bị</button></form><form method="post" action="/admin/keys/{key}/revoke"><button class="danger">Thu hồi key</button></form></div></div><br><div class="card"><h2>Thiết bị và lịch sử dùng key</h2><div class="tablewrap"><table class="table"><tr><th>Device</th><th>IP</th><th>Trình duyệt</th><th>Lần cuối</th><th>Trạng thái</th></tr>{dev or '<tr><td colspan="5" class="empty">Chưa có thiết bị</td></tr>'}</table></div></div>'''
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
def missing(e): return jsonify(ok=False,error='not_found',message='Không tìm thấy endpoint'),404 if request.path.startswith('/api/') or request.path.startswith('/tx/api/') else (page('404','<h1>Không tìm thấy trang</h1>'),404)
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT','5000')))
