import argparse,json,os,tempfile
from pathlib import Path
import pandas as pd
from .db import ROOT,DEFAULT_DB,connect
from .sample import generate
from .quality import validate
def create(db=DEFAULT_DB,seed=42,data=None):
    db=Path(db).resolve()
    if db.exists():raise FileExistsError('Không ghi đè database: '+str(db))
    db.parent.mkdir(parents=True,exist_ok=True);data=generate(seed) if data is None else data
    fd,tmp=tempfile.mkstemp(dir=db.parent,suffix='.db');os.close(fd)
    try:
        with connect(tmp,False) as c:
            c.executescript((ROOT/'sql/schema.sql').read_text(encoding='utf-8'))
            for table,n in [('players',2),('levels',3),('sessions',4),('level_attempts',6)]:c.executemany('INSERT INTO '+table+' VALUES('+','.join('?' for _ in range(n))+')',data[table])
            c.executemany('INSERT INTO metadata VALUES(?,?)',{'data_kind':'simulated','seed':str(seed),'version':'1.0.0','start':'2026-01-01','end':'2026-03-31 23:59:59','timezone':'Asia/Ho_Chi_Minh','activity_day_rule':'date(session.started_at)','retention_rule':'exact day since first session; only matured players'}.items())
        validate(tmp);os.link(tmp,db)
    finally:Path(tmp).unlink(missing_ok=True)
    return validate(db)
def prepare(db=DEFAULT_DB,raw_out=None):
    if not Path(db).exists():create(db)
    q=validate(db);out=Path(raw_out or ROOT/'data/raw');out.mkdir(parents=True,exist_ok=True)
    with connect(db) as c:
        for table in ['players','levels','sessions','level_attempts','metadata']:pd.read_sql_query('SELECT * FROM '+table,c).to_csv(out/(table+'.csv'),index=False,encoding='utf-8-sig')
    print('GIẢ LẬP — giữ nguyên DB nếu đã có; CSV nguồn:',out);print(q.to_string(index=False));return q
def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default=str(DEFAULT_DB));p.add_argument('--raw-out');a=p.parse_args();prepare(a.db,a.raw_out)
if __name__=='__main__':main()
