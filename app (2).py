import os,secrets,string,json
from datetime import datetime,timezone,timedelta
from flask import Flask,request,jsonify,Response,redirect
from core import *
app=Flask(__name__);app.secret_key=os.getenv('SECRET_KEY','dev-secret-change-me');init_db();seed()
CSS='''*{box-sizing:border-box}body{margin:0;background:#0a0a0a;color:#fafafa;font:15px system-ui,sans-serif}a{color:inherit;text-decoration:none}.top{position:sticky;top:0;height:58px;padding:0 20px;display:flex;align-items:center;gap:20px;background:#111;border-bottom:1px solid #292929;z-index:2}.logo{font-weight:800;letter-spacing:.15em;margin-right:auto}.nav{display:flex;gap:16px;color:#aaa}.wrap{max-width:1180px;margin:auto;padding:30px 20px}.hero{text-align:center;padding:50px 0}.hero h1{font-size:clamp(48px,10vw,92px);letter-spacing:.15em;margin:20px 0 8px}.muted{color:#aaa}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.card{background:#131313;border:1px solid #292929;border-radius:15px;padding:18px;box-shadow:inset 0 1px #333}.row{display:flex;gap:14px;align-items:center;border-bottom:1px solid #292929;padding:10px 0}.row span:last-child{margin-left:auto;color:#aaa}input,select,button{padding:11px 13px;border-radius:8px;border:1px solid #3a3a3a;background:#1b1b1b;color:#fff}button{background:#eee;color:#111;font-weight:700;cursor:pointer}.form{display:flex;gap:10px;margin:20px 0}.form input{flex:1}.danger{color:#ff9b9b}.code{font-size:90px;font-weight:800;text-align:center}@media(max-width:767px){.grid{grid-template-columns:1fr 1fr}.nav{gap:8px;font-size:13px}.form{display:block}.form>*{width:100%;margin:4px 0}}'''
def html(title,body):return f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body><header class="top"><a class="logo" href="/">PAWNOVA</a><nav class="nav"><a href="/">Trang chủ</a><a href="/pricing">Bảng giá</a><a href="/support">Hỗ trợ</a><a href="/admin">Admin</a></nav></header><main class="wrap">{body}</main></body></html>'''
def table_for(game,typ):return row('SELECT t.*,g.name game_name FROM tables_ t JOIN games g ON g.code=t.game_code WHERE t.code=?',(f'{game}_{typ}',))
def result(r):return {'phien':r['session_id'],'dudoan':r['prediction'],'ketqua':r['actual'] or 'chuacoketqua','trangthai':'win✅' if r['result']=='win' else 'lose❌' if r['result']=='lose' else ''}
def admin_auth():
 a=request.authorization
 if not a or a.username!=os.getenv('ADMIN_USER','admin') or a.password!=os.getenv('ADMIN_PASS','change-me'):return Response('Yêu cầu đăng nhập',401,{'WWW-Authenticate':'Basic realm="PAWNOVA Admin"'})
@app.after_request
def cors(r):
 if request.path.startswith('/api/'):r.headers.update({'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET, POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type, X-API-Key, X-Device-Id'})
 return r
@app.get('/')
def home():
 gs=rows('SELECT * FROM games ORDER BY sort_order');ts=rows('SELECT * FROM tables_ ORDER BY sort_order');cards=''.join('<article class="card"><h2>'+g['name']+'</h2>'+''.join(f'<div class="row"><b>{t["table_type"].upper()}</b><span>•••</span><small class="muted">Nhập key để xem</small></div>' for t in ts if t['game_code']==g['code'])+'</article>' for g in gs)
 return html('PAWNOVA','<section class="hero"><p class="muted">6 game · 11 bàn</p><h1>PAWNOVA</h1><p class="muted">Bot tự học pattern dự đoán Tài Xỉu</p><form class="form" action="/tx/api/ma"><input name="key" placeholder="Nhập API key"><button>Xem key</button></form></section><section class="grid">'+cards+'</section>')
@app.get('/pricing')
def pricing():return html('Bảng giá','<h1>Bảng giá</h1><section class="grid"><article class="card">Từng bàn<strong>50.000đ/tuần</strong></article><article class="card">Gói game<strong>80.000đ/tuần</strong></article><article class="card">ALL — 11 bàn<strong>350.000đ/tuần</strong></article></section>')
@app.get('/support')
def support():return html('Hỗ trợ','<h1>Hỗ trợ</h1><article class="card"><h2>API key dùng thế nào?</h2><p>Gửi key qua X-API-Key hoặc tham số key.</p><h2>Thiết bị bị khóa?</h2><p>Chờ hết thời gian idle hoặc liên hệ admin.</p></article>')
@app.route('/tx/api/ma',methods=['GET','POST'])
def key_page():
 key=request.values.get('key','');k=row('SELECT * FROM api_keys WHERE key=?',(key,))
 if not k:return html('404','<div class="code">404</div><h1>API key không tồn tại</h1>'),404
 msg=''
 if request.method=='POST':
  code=request.form.get('code','').upper();c=row('SELECT * FROM activation_codes WHERE code=?',(code,))
  if not c or c['revoked'] or (c['expires_at'] and c['expires_at']<=now_iso()) or (c['max_uses']!=-1 and c['used_count']>=c['max_uses']):msg='Mã kích hoạt không hợp lệ hoặc đã hết hạn'
  else:
   exp=(datetime.now(timezone.utc)+timedelta(days=c['days'])).replace(microsecond=0).isoformat().replace('+00:00','Z')
   with db() as x:x.execute('UPDATE activation_codes SET used_count=used_count+1 WHERE code=?',(code,));x.execute('UPDATE api_keys SET scope=?,expires_at=?,is_active=1 WHERE key=?',(c['scope'],exp,key))
   k=row('SELECT * FROM api_keys WHERE key=?',(key,))
 body=f'<h1>API Key</h1><article class="card"><p class="mono">{k["key"]}</p><p>Scope: {k["scope"]}</p><p>Hạn: {k["expires_at"] or "Chưa kích hoạt"}</p>'
 if not k['is_active'] or msg:body+=f'<p class="danger">{msg or "Key chưa kích hoạt"}</p><form class="form" method="post"><input type="hidden" name="key" value="{key}"><input name="code" placeholder="Mã kích hoạt"><button>Kích hoạt</button></form>'
 return html('API Key',body+'</article>')
def auth_api(t,admin=False):
 return Auth.key(t['code'],admin)
@app.get('/api/<game>/<typ>/ma')
def api_prediction(game,typ):
 t=table_for(game,typ)
 if not t:return jsonify(error='not_found',message='Bàn không tồn tại'),404
 k,e=auth_api(t)
 if e:return e
 r=row('SELECT session_id,prediction,actual,result FROM predictions WHERE table_code=? ORDER BY session_id DESC LIMIT 1',(t['code'],));return jsonify({'admin':'P A W','telegram':'@K0ZT1',**(result(r) if r else {'phien':0,'dudoan':None,'ketqua':'chuacoketqua','trangthai':''})})
@app.get('/api/<game>/<typ>/history')
def api_history(game,typ):
 t=table_for(game,typ)
 if not t:return jsonify(error='not_found',message='Bàn không tồn tại'),404
 k,e=auth_api(t)
 if e:return e
 rs=rows('SELECT session_id,prediction,actual,result FROM predictions WHERE table_code=? AND actual IS NOT NULL ORDER BY session_id DESC LIMIT 50',(t['code'],));return jsonify(count=len(rs),items=[result(x) for x in rs])
@app.get('/api/<game>/<typ>/chitiet')
def api_detail(game,typ):
 t=table_for(game,typ)
 if not t:return jsonify(error='not_found',message='Bàn không tồn tại'),404
 k,e=auth_api(t,True)
 if e:return e
 return jsonify(table_code=t['code'],game=game,game_name=t['game_name'],table=typ,upstream_url=t['upstream_url'])
@app.get('/admin')
def admin_home():
 e=admin_auth()
 if e:return e
 return html('Admin','<h1>Dashboard</h1><section class="grid"><article class="card">Total Keys<strong>'+str(len(rows('SELECT * FROM api_keys')))+ '</strong></article><article class="card">Games<strong>6</strong></article><article class="card">Tables<strong>11</strong></article></section>')
@app.get('/admin/keys')
def admin_keys():
 e=admin_auth()
 if e:return e
 ks=rows('SELECT * FROM api_keys ORDER BY created_at DESC');items=''.join(f'<div class="card row"><span>{k["key"]}</span><span>{k["scope"]}</span><span>{"Hoạt động" if k["is_active"] else "Đã khóa"}</span></div>' for k in ks)
 return html('Keys','<h1>Keys</h1><form class="card form" method="post" action="/admin/keys/create"><select name="scope"><option>ALL</option><option>68gb</option><option>b52</option><option>sunwin</option><option>max789</option><option>lc79</option><option>betvip</option></select><input name="note" placeholder="Ghi chú"><button>Tạo key</button></form>'+items)
@app.post('/admin/keys/create')
def create_key():
 e=admin_auth()
 if e:return e
 key='TXLIVE_'+''.join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(24))
 with db() as c:c.execute('INSERT INTO api_keys(key,scope,note,is_active) VALUES(?,?,?,0)',(key,request.form.get('scope','ALL'),request.form.get('note','')))
 return redirect('/admin/keys')
@app.get('/admin/codes')
def admin_codes():
 e=admin_auth()
 if e:return e
 cs=rows('SELECT * FROM activation_codes ORDER BY created_at DESC');items=''.join(f'<div class="card row"><span>{c["code"]}</span><span>{c["scope"]}</span><span>{c["days"]} ngày</span></div>' for c in cs)
 return html('Codes','<h1>Codes</h1><form class="card form" method="post" action="/admin/codes/create"><select name="scope"><option>ALL</option><option>68gb</option><option>b52</option><option>sunwin</option></select><input name="days" type="number" value="7"><button>Tạo code</button></form>'+items)
@app.post('/admin/codes/create')
def create_code():
 e=admin_auth()
 if e:return e
 a='23456789ABCDEFGHJKMNPQRSTUVWXYZ';code='TX'+''.join(secrets.choice(a) for _ in range(10))
 with db() as c:c.execute('INSERT INTO activation_codes(code,scope,days,created_by) VALUES(?,?,?,?)',(code,request.form.get('scope','ALL'),int(request.form.get('days',7)),'admin'))
 return redirect('/admin/codes')
@app.get('/admin/monitor')
def admin_monitor():
 e=admin_auth()
 if e:return e
 ts=rows('SELECT * FROM tables_ ORDER BY sort_order');return html('Monitor','<h1>Monitor</h1><section class="grid">'+''.join(f'<article class="card"><h3>{t["code"]}</h3><p>Đang theo dõi</p></article>' for t in ts)+'</section>')
@app.get('/admin/api/monitor')
def monitor_api():
 e=admin_auth()
 if e:return e
 data=[]
 for t in rows('SELECT * FROM tables_ ORDER BY sort_order'):
  p=rows("SELECT result FROM predictions WHERE table_code=? AND actual IS NOT NULL ORDER BY session_id DESC LIMIT 100",(t['code'],));w=sum(x['result']=='win' for x in p);data.append({'code':t['code'],'predictions_total':len(p),'wins':w,'losses':len(p)-w,'accuracy_100':w/max(1,len(p))})
 return jsonify(summary={'total':len(data),'active':len(data)},tables=data,alerts=[])
@app.route('/api/<path:x>',methods=['OPTIONS'])
def options(x):return '',204
@app.errorhandler(404)
def missing(e):return html('404','<div class="code">404</div><h1>Không tìm thấy trang</h1>'),404
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.getenv('PORT','5000')))
