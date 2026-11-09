import os,secrets,string,json,requests
from datetime import datetime,timezone,timedelta
from flask import Flask,render_template,request,jsonify,redirect,url_for
from core import *
app=Flask(__name__);app.secret_key=os.getenv('SECRET_KEY','dev-secret-change-me');init_db();seed()
def tab(game,typ):return row('SELECT t.*,g.name game_name FROM tables_ t JOIN games g ON g.code=t.game_code WHERE t.code=?',(f'{game}_{typ}',))
def out(r):return {'phien':r['session_id'],'dudoan':r['prediction'],'ketqua':r['actual'] or 'chuacoketqua','trangthai':'win✅' if r['result']=='win' else 'lose❌' if r['result']=='lose' else ''}
@app.after_request
def cors(r):
 if request.path.startswith('/api/'):r.headers.update({'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET, POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type, X-API-Key, X-Device-Id'})
 return r
@app.get('/')
def home():return render_template('pages.html',page='home',games=rows('SELECT * FROM games ORDER BY sort_order'),tables=rows('SELECT * FROM tables_ ORDER BY sort_order'))
@app.get('/pricing')
def pricing():return render_template('pages.html',page='pricing')
@app.get('/support')
def support():return render_template('pages.html',page='support')
@app.route('/tx/api/ma',methods=['GET','POST'])
def key_page():
 key=request.values.get('key','');k=row('SELECT * FROM api_keys WHERE key=?',(key,))
 if not k:return render_template('pages.html',page='error',code=404,title='Không tìm thấy',message='API key không tồn tại'),404
 if request.method=='POST':
  code=request.form.get('code','').upper();c=row('SELECT * FROM activation_codes WHERE code=?',(code,))
  if not c or c['revoked'] or (c['expires_at'] and c['expires_at']<=now_iso()) or (c['max_uses']!=-1 and c['used_count']>=c['max_uses']):return render_template('pages.html',page='key',key=k,error='Mã kích hoạt không hợp lệ hoặc đã hết hạn'),400
  exp=(datetime.now(timezone.utc)+timedelta(days=c['days'])).replace(microsecond=0).isoformat().replace('+00:00','Z')
  with db() as x:x.execute('UPDATE activation_codes SET used_count=used_count+1 WHERE code=?',(code,));x.execute('UPDATE api_keys SET scope=?,expires_at=?,is_active=1 WHERE key=?',(c['scope'],exp,key));x.execute('INSERT INTO activation_log(key,code,success,reason) VALUES(?,?,1,?)',(key,code,'ok'))
  return redirect(url_for('key_page',key=key))
 return render_template('pages.html',page='key',key=k)
@app.route('/api/<game>/<typ>/ma')
def predict(game,typ):
 t=tab(game,typ)
 if not t:return jsonify(error='not_found',message='Bàn không tồn tại'),404
 k,e=Auth.key(t['code']);
 if e:return e
 r=row('SELECT session_id,prediction,actual,result FROM predictions WHERE table_code=? ORDER BY session_id DESC LIMIT 1',(t['code'],));return jsonify({'admin':'P A W','telegram':'@K0ZT1',**(out(r) if r else {'phien':0,'dudoan':None,'ketqua':'chuacoketqua','trangthai':''})})
@app.get('/api/<game>/<typ>/history')
def history(game,typ):
 t=tab(game,typ)
 if not t:return jsonify(error='not_found',message='Bàn không tồn tại'),404
 k,e=Auth.key(t['code']);
 if e:return e
 r=rows('SELECT session_id,prediction,actual,result FROM predictions WHERE table_code=? AND actual IS NOT NULL ORDER BY session_id DESC LIMIT 50',(t['code'],));return jsonify(count=len(r),items=[out(x) for x in r])
@app.get('/api/<game>/<typ>/chitiet')
def detail(game,typ):
 t=tab(game,typ)
 if not t:return jsonify(error='not_found',message='Bàn không tồn tại'),404
 k,e=Auth.key(t['code'],True)
 if e:return e
 return jsonify(table_code=t['code'],game=game,game_name=t['game_name'],table=typ,upstream_url=t['upstream_url'])
@app.get('/admin')
@Auth.admin
def admin():return render_template('pages.html',page='admin',keys=rows('SELECT * FROM api_keys ORDER BY created_at DESC'),games=rows('SELECT * FROM games ORDER BY sort_order'))
@app.get('/admin/keys')
@Auth.admin
def admin_keys():return render_template('pages.html',page='keys',keys=rows('SELECT * FROM api_keys ORDER BY created_at DESC'))
@app.post('/admin/keys/create')
@Auth.admin
def create_key():
 k='TXLIVE_'+''.join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(24))
 with db() as c:c.execute('INSERT INTO api_keys(key,scope,note,is_active) VALUES(?,?,?,0)',(k,request.form.get('scope','ALL'),request.form.get('note','')))
 return redirect('/admin/keys')
@app.post('/admin/keys/<key>/revoke')
@Auth.admin
def revoke(key):
 with db() as c:c.execute('UPDATE api_keys SET is_active=0 WHERE key=?',(key,))
 return redirect('/admin/keys')
@app.get('/admin/codes')
@Auth.admin
def codes():return render_template('pages.html',page='codes',codes=rows('SELECT * FROM activation_codes ORDER BY created_at DESC'))
@app.post('/admin/codes/create')
@Auth.admin
def create_code():
 a='23456789ABCDEFGHJKMNPQRSTUVWXYZ';code='TX'+''.join(secrets.choice(a) for _ in range(10))
 with db() as c:c.execute('INSERT INTO activation_codes(code,scope,days,created_by) VALUES(?,?,?,?)',(code,request.form.get('scope','ALL'),int(request.form.get('days',7)),'admin'))
 return redirect('/admin/codes')
@app.get('/admin/games')
@Auth.admin
def games_admin():return render_template('pages.html',page='games',games=rows('SELECT * FROM games ORDER BY sort_order'),tables=rows('SELECT * FROM tables_ ORDER BY sort_order'))
@app.get('/admin/monitor')
@Auth.admin
def monitor():return render_template('pages.html',page='monitor',tables=rows('SELECT * FROM tables_ ORDER BY sort_order'))
@app.get('/admin/logs')
@Auth.admin
def logs():return render_template('pages.html',page='logs',logs=rows('SELECT * FROM admin_actions ORDER BY id DESC LIMIT 200'))
@app.get('/admin/api/monitor')
@Auth.admin
def monitor_api():
 d=[]
 for t in rows('SELECT * FROM tables_ ORDER BY sort_order'):
  p=rows("SELECT result FROM predictions WHERE table_code=? AND actual IS NOT NULL ORDER BY session_id DESC LIMIT 100",(t['code'],));w=sum(x['result']=='win' for x in p);d.append({'code':t['code'],'predictions_total':len(p),'wins':w,'losses':len(p)-w,'accuracy_100':w/max(1,len(p))})
 return jsonify(summary={'total':len(d),'active':sum(1 for x in d if x['predictions_total']>=0)},tables=d,alerts=[])
@app.route('/api/<path:x>',methods=['OPTIONS'])
def options(x):return '',204
@app.errorhandler(404)
def missing(e):return render_template('pages.html',page='error',code=404,title='Không tìm thấy',message='Trang không tồn tại'),404
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.getenv('PORT','5000')))
