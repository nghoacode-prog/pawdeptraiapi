import json,time,logging,requests
from core import *
log=logging.getLogger('worker');logging.basicConfig(level=logging.INFO)
def process(t):
 try:r=requests.get(t['upstream_url'],timeout=10);r.raise_for_status();p=parse(r.json())
 except Exception as e:log.warning('%s: %s',t['code'],e);return
 if not p:return
 with db() as c:
  s=c.execute('SELECT * FROM table_states WHERE table_code=?',(t['code'],)).fetchone();last=s['last_seen_id'] or 0;hist=json.loads(s['history_json'] or '[]');eng=Engine(hist);cur=p['session_id'];incoming=p['history'];first=cur-len(incoming)+1
  if cur<=last:return
  for sid in range(max(last+1,first),cur+1):
   y=incoming[sid-first];actual='TAI' if y else 'XIU';old=c.execute('SELECT * FROM predictions WHERE table_code=? AND session_id=? AND actual IS NULL',(t['code'],sid)).fetchone()
   if old:c.execute('UPDATE predictions SET actual=?,result=?,resolved_at=? WHERE id=?',(actual,'win' if old['prediction']==actual else 'lose',now_iso(),old['id']))
   eng.observe(y);q=eng.predict();c.execute('INSERT OR IGNORE INTO predictions(table_code,session_id,prediction,confidence) VALUES(?,?,?,?)',(t['code'],sid+1,q['side'],q['confidence']))
  c.execute('UPDATE table_states SET history_json=?,last_seen_id=?,updated_at=?,last_poll_at=? WHERE table_code=?',(json.dumps((hist+incoming)[-2000:]),cur,now_iso(),now_iso(),t['code']))
def main():
 init_db();seed()
 while True:
  for t in rows('SELECT * FROM tables_ WHERE is_active=1 ORDER BY sort_order'):process(t)
  time.sleep(60)
if __name__=='__main__':main()
