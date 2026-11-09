import os,json,math,time,hashlib,sqlite3
from contextlib import contextmanager
from datetime import datetime,timezone
from functools import wraps
from flask import request,jsonify,Response
DB_PATH=os.getenv('DATABASE_PATH',os.path.join(os.path.dirname(__file__),'data','app.db'))
def now_iso():return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def connect():
 os.makedirs(os.path.dirname(DB_PATH) or '.',exist_ok=True);c=sqlite3.connect(DB_PATH,timeout=30);c.row_factory=sqlite3.Row;c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA foreign_keys=ON');return c
@contextmanager
def db():
 c=connect()
 try:yield c;c.commit()
 except Exception:c.rollback();raise
 finally:c.close()
def rows(sql,a=()):
 with db() as c:return c.execute(sql,a).fetchall()
def row(sql,a=()):
 with db() as c:return c.execute(sql,a).fetchone()
def init_db():
 with db() as c:c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE,created_at TEXT DEFAULT CURRENT_TIMESTAMP);CREATE TABLE IF NOT EXISTS games(code TEXT PRIMARY KEY,name TEXT NOT NULL,sort_order INT DEFAULT 0,is_active INT DEFAULT 1);CREATE TABLE IF NOT EXISTS tables_(code TEXT PRIMARY KEY,game_code TEXT NOT NULL REFERENCES games(code),table_type TEXT NOT NULL,upstream_url TEXT NOT NULL,sort_order INT DEFAULT 0,is_active INT DEFAULT 1);CREATE INDEX IF NOT EXISTS idx_tables_game ON tables_(game_code,sort_order);CREATE TABLE IF NOT EXISTS table_states(table_code TEXT PRIMARY KEY REFERENCES tables_(code),history_json TEXT,last_seen_id INTEGER DEFAULT 0,updated_at TEXT DEFAULT CURRENT_TIMESTAMP,last_poll_at TEXT);CREATE TABLE IF NOT EXISTS predictions(id INTEGER PRIMARY KEY AUTOINCREMENT,table_code TEXT NOT NULL,session_id INTEGER NOT NULL,prediction TEXT NOT NULL,confidence INTEGER NOT NULL,actual TEXT,result TEXT,resolved_at TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(table_code,session_id));CREATE INDEX IF NOT EXISTS idx_pred_table ON predictions(table_code,session_id DESC);CREATE TABLE IF NOT EXISTS api_keys(key TEXT PRIMARY KEY,scope TEXT NOT NULL,note TEXT,is_active INT DEFAULT 1,is_admin INT DEFAULT 0,expires_at TEXT,max_devices INT DEFAULT 1,created_at TEXT DEFAULT CURRENT_TIMESTAMP,last_used_at TEXT);CREATE TABLE IF NOT EXISTS api_key_devices(id INTEGER PRIMARY KEY AUTOINCREMENT,key TEXT NOT NULL REFERENCES api_keys(key),device_id TEXT NOT NULL,ip TEXT,user_agent TEXT,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL,released_at TEXT,released_reason TEXT);CREATE INDEX IF NOT EXISTS idx_devices_key ON api_key_devices(key,released_at);CREATE TABLE IF NOT EXISTS activation_codes(code TEXT PRIMARY KEY,scope TEXT NOT NULL,days INT NOT NULL,max_uses INT DEFAULT -1,used_count INT DEFAULT 0,expires_at TEXT,created_by TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,revoked INT DEFAULT 0);CREATE TABLE IF NOT EXISTS activation_log(id INTEGER PRIMARY KEY AUTOINCREMENT,key TEXT,code TEXT,success INT,ip TEXT,user_agent TEXT,reason TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);CREATE TABLE IF NOT EXISTS admin_actions(id INTEGER PRIMARY KEY AUTOINCREMENT,admin_user TEXT,action TEXT,target TEXT,detail_json TEXT,ip TEXT,user_agent TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);CREATE TABLE IF NOT EXISTS engine_resets(id INTEGER PRIMARY KEY AUTOINCREMENT,table_code TEXT NOT NULL,reason TEXT NOT NULL,accuracy_before REAL,accuracy_after REAL,sessions_at_reset INT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);''')
GAMES=[('68gb','68GB',1),('b52','B52',2),('sunwin','SUNWIN',3),('max789','MAX789',4),('lc79','LC79',5),('betvip','BETVIP',6)]
TABLES=[('68gb_tx','68gb','tx','http://180.93.114.133:5000/68tx/api/tx',1),('68gb_md5','68gb','md5','http://180.93.114.133:5000/68md5/api/md5',2),('b52_tx','b52','tx','http://180.93.114.133:5000/b52/api/tx',3),('b52_md5','b52','md5','http://180.93.114.133:5000/b52/api/md5',4),('sunwin_tx','sunwin','tx','http://180.93.114.133:5000/sunwin/api/tx',5),('max789_tx','max789','tx','http://180.93.114.133:5000/max789/api/tx',6),('max789_md5','max789','md5','http://180.93.114.133:5000/max789/api/md5',7),('lc79_tx','lc79','tx','http://180.93.114.133:5000/lc79/api/tx',8),('lc79_md5','lc79','md5','http://180.93.114.133:5000/lc79/api/md5',9),('betvip_tx','betvip','tx','http://180.93.114.133:5000/betvip/api/tx',10),('betvip_md5','betvip','md5','http://180.93.114.133:5000/betvip/api/md5',11)]
def seed():
 with db() as c:
  c.executemany('INSERT OR IGNORE INTO games(code,name,sort_order) VALUES(?,?,?)',GAMES);c.executemany('INSERT OR IGNORE INTO tables_(code,game_code,table_type,upstream_url,sort_order) VALUES(?,?,?,?,?)',TABLES);c.executemany('INSERT OR IGNORE INTO table_states(table_code,history_json) VALUES(?,?)',[(x[0],'[]') for x in TABLES])
def parse(raw):
 if not isinstance(raw,dict):return None
 try:sid=int(raw.get('phien',raw.get('phien_id',raw.get('session_id',0))) or 0)
 except (ValueError,TypeError):return None
 if sid<=0:return None
 k=str(raw.get('ket_qua',raw.get('ketqua',raw.get('result','')))).strip().lower()
 tong=raw.get('tong',raw.get('total',raw.get('sum')))
 try:tong=int(str(tong).strip()) if tong not in (None,'') else None
 except (ValueError,TypeError):tong=None
 r=1 if k in ('tài','tai','tài','t','tai xiu tai') else 0 if k in ('xỉu','xiu','xỉu','x','tai xiu xiu') else (1 if tong is not None and 11<=tong<=18 else 0 if tong is not None and 3<=tong<=10 else None)
 if r is None:return None
 cau=str(raw.get('cau',raw.get('chuoi',''))).upper();h=[1 if x=='T' else 0 for x in cau if x in 'TX'] or [r];return {'session_id':sid,'result':r,'history':h}
def clamp(v):return max(.001,min(.999,float(v)))
def logit(p):return math.log(clamp(p)/(1-clamp(p)))
def sigmoid(x):return 1/(1+math.exp(-max(-40,min(40,x))))
class Engine:
 EXPERTS=('ngram','streak','ema','markov','cycle')
 def __init__(self,h=None):
  self.history=list(h or [])[-2000:];self.weights={x:.2 for x in self.EXPERTS};self.expert_scores={x:.5 for x in self.EXPERTS};self.samples=0;self.regime_change=False;self.learn()
 def expert(self,h):
  if not h:return {'ngram':(.5,1),'streak':(.5,1),'ema':(.5,1),'markov':(.5,1),'cycle':(.5,1)}
  n=[]
  for k in range(1,min(10,len(h))+1):
   ctx=tuple(h[-k:]);m=[h[i] for i in range(k,len(h)) if tuple(h[i-k:i])==ctx]
   if m:n.append((sum(m)+1)/(len(m)+2))
  p=.5;a=1-math.pow(.5,1/50)
  for x in h:p=a*x+(1-a)*p
  prev=h[-1];m=[h[i] for i in range(1,len(h)) if h[i-1]==prev];mark=(sum(m)+1)/(len(m)+2) if m else .5
  side=h[-1];run=next((i for i,x in enumerate(reversed(h)) if x!=side),len(h));cont=sum(h[i]==h[i-1] for i in range(1,len(h)));br=len(h)-1-cont;pc=(cont+1)/(cont+br+2);st=pc if side else 1-pc
  cyc=.5
  for per in range(2,9):
   if len(h)>5*per:
    w=h[-5*per:];rate=sum(w[i]==w[i-per] for i in range(per,len(w)))/max(1,len(w)-per)
    if rate>=.55:cyc=.5+(rate-.5)*2*(h[-per]-.5)*1.5
  return {'ngram':(n[-1] if n else (sum(h)+1)/(len(h)+2),max(1,len(n)*2)),'streak':(st,max(1,cont+br)),'ema':(p,1/a),'markov':(mark,max(1,len(m))),'cycle':(cyc,3.5)}
 def learn(self):
  h=self.history[-500:]
  if len(h)<25:return
  scores={x:0.0 for x in self.EXPERTS};counts=0;recent=[];start=max(20,len(h)-240)
  for i in range(start,len(h)):
   e=self.expert(h[:i]);y=h[i];decay=0.992**(len(h)-1-i);counts+=decay
   for k,(p,_) in e.items():scores[k]+=decay*(1-((p-y)**2))
   if i>=len(h)-35:
    recent.append(sum((e[k][0]>=.5)==bool(y) for k in self.EXPERTS)/len(self.EXPERTS))
  self.samples=round(counts);self.expert_scores={k:max(.05,min(.95,scores[k]/max(counts,.001))) for k in self.EXPERTS}
  raw={k:math.exp((self.expert_scores[k]-.5)*7) for k in self.EXPERTS};total=sum(raw.values());self.weights={k:raw[k]/total for k in self.EXPERTS}
  self.regime_change=bool(recent and sum(recent)/len(recent)<.45)
 def predict(self):
  h=self.history[-2000:];self.learn();e=self.expert(h);num=sum(self.weights[k]*v[1]*logit(v[0]) for k,v in e.items());den=sum(self.weights[k]*v[1] for k,v in e.items());p=sigmoid(num/max(den,.001));ps=self._pool(h[-100:]);pl=self._pool(h[-500:]);p=.5 if (ps-.5)*(pl-.5)<0 else p
  side='TAI' if p>=.5 else 'XIU';edge=min(abs(p-.5)*2,.3 if len(h)<100 else .5 if len(h)<500 else .7);confidence=max(58,min(72,round(58+edge*14)))
  return {'side':side,'confidence':confidence,'p_internal':p,'experts':e,'weights':self.weights,'learning':{'samples':self.samples,'scores':self.expert_scores,'regime_change':self.regime_change}}
 def _pool(self,h):
  e=self.expert(h);return sigmoid(sum(self.weights[k]*v[1]*logit(v[0]) for k,v in e.items())/max(.001,sum(self.weights[k]*v[1] for k,v in e.items())))
 def observe(self,y):self.history=(self.history+[int(y)])[-2000:]
class Auth:
 rate={}
 @staticmethod
 def scope(scope,table):return scope=='ALL' or scope==table or scope==table.rsplit('_',1)[0]
 @staticmethod
 def admin(fn):
  @wraps(fn)
  def w(*a,**k):
   x=request.authorization
   if not x or x.username!=os.getenv('ADMIN_USER','admin') or x.password!=os.getenv('ADMIN_PASS','change-me'):return Response('Yêu cầu đăng nhập',401,{'WWW-Authenticate':'Basic realm="PAWNOVA Admin"'})
   return fn(*a,**k)
  return w
 @staticmethod
 def key(table,admin=False):
  key=request.headers.get('X-API-Key') or request.args.get('key');k=row('SELECT * FROM api_keys WHERE key=?',(key,)) if key else None
  if not k:return None,(jsonify(error='login_required',message='Thiếu hoặc sai API key'),401)
  if admin and not k['is_admin']:return None,(jsonify(error='admin_required',message='Không có quyền admin'),403)
  if not admin and (not k['is_active'] or (k['expires_at'] and k['expires_at']<=now_iso())):return None,(jsonify(error='no_access',message='Key chưa kích hoạt hoặc hết hạn',scope_needed=table),403)
  if not admin and not Auth.scope(k['scope'],table):return None,(jsonify(error='no_access',message='Chưa kích hoạt',scope_needed=table),403)
  bucket=int(time.time()//60);rk=(key,bucket);Auth.rate[rk]=Auth.rate.get(rk,0)+1
  if Auth.rate[rk]>int(os.getenv('RATE_LIMIT_PER_MINUTE','60')):return None,(jsonify(error='rate_limited',message='Quá nhiều yêu cầu'),429)
  if not admin and k['max_devices'] and os.getenv('DEVICE_LOCK_ENABLED','1')=='1':
   did=request.headers.get('X-Device-Id') or hashlib.sha256((request.remote_addr+'|'+request.user_agent.string).encode()).hexdigest()[:32];now=now_iso()
   with db() as c:
    a=c.execute("SELECT * FROM api_key_devices WHERE key=? AND released_at IS NULL",(key,)).fetchone()
    if a and a['device_id']!=did:
     idle=(datetime.now(timezone.utc)-datetime.fromisoformat(a['last_seen'].replace('Z','+00:00'))).total_seconds()/60
     if idle<int(os.getenv('DEVICE_IDLE_MINUTES','10')):return None,(jsonify(error='device_locked',message='Key đang dùng trên thiết bị khác',retry_after_minutes=1),423)
     c.execute("UPDATE api_key_devices SET released_at=?,released_reason='idle' WHERE id=?",(now,a['id']))
    c.execute('INSERT INTO api_key_devices(key,device_id,ip,user_agent,first_seen,last_seen) VALUES(?,?,?,?,?,?) ON CONFLICT DO NOTHING',(key,did,request.remote_addr,request.user_agent.string,now,now));c.execute('UPDATE api_keys SET last_used_at=? WHERE key=?',(now,key))
  return k,None
