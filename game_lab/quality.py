import re
from datetime import datetime
import pandas as pd
from .db import connect
from .sample import START,END
def timestamp(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',value):raise ValueError('Ngày giờ cần YYYY-MM-DD HH:MM:SS: '+str(value))
    return datetime.strptime(value,'%Y-%m-%d %H:%M:%S')
def validate(db):
    with connect(db) as c:
        if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or c.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Database/khóa ngoại không hợp lệ')
        players=pd.read_sql_query('SELECT * FROM players',c);levels=pd.read_sql_query('SELECT * FROM levels ORDER BY level_order',c)
        sessions=pd.read_sql_query('SELECT * FROM sessions ORDER BY player_id,started_at,session_id',c)
        attempts=pd.read_sql_query('SELECT a.*,s.player_id FROM level_attempts a JOIN sessions s USING(session_id) ORDER BY s.player_id,a.started_at,a.attempt_id',c)
        metadata=dict(c.execute('SELECT * FROM metadata'))
    if metadata.get('data_kind')!='simulated':raise ValueError('Thiếu nhãn GIẢ LẬP')
    if list(levels.level_order)!=list(range(1,len(levels)+1)):raise ValueError('Thứ tự màn cần liên tục từ 1')
    session_map={};last_end={}
    for row in sessions.itertuples(index=False):
        try:start,end=timestamp(row.started_at),timestamp(row.ended_at)
        except ValueError as e:raise ValueError(f'Phiên {row.session_id}: {e}') from e
        if not START<=start<end<=END:raise ValueError(f'Thời gian phiên {row.session_id} ngoài kỳ hoặc không dương')
        if row.player_id in last_end and start<last_end[row.player_id]:raise ValueError(f'Phiên chồng nhau của người {row.player_id}')
        last_end[row.player_id]=end;session_map[row.session_id]=(start,end)
    orders=dict(zip(levels.level_id,levels.level_order));completed={};attempt_end={}
    for row in attempts.itertuples(index=False):
        start,end=timestamp(row.started_at),timestamp(row.ended_at);ss,se=session_map[row.session_id]
        if not ss<=start<end<=se:raise ValueError(f'Lượt thử {row.attempt_id} ngoài phiên hoặc không dương')
        if start<attempt_end.get(row.session_id,ss):raise ValueError(f'Lượt thử chồng nhau: {row.attempt_id}')
        attempt_end[row.session_id]=end
        order=orders[row.level_id]
        if order>1 and (row.player_id,order-1) not in completed:raise ValueError(f'Mở màn trước khi hoàn thành màn trước: {row.attempt_id}')
        if row.result not in ('failed','completed'):raise ValueError('Kết quả không hợp lệ')
        if row.result=='completed':completed[(row.player_id,order)]=True
    seen=set(sessions.player_id)
    info={'players':len(players),'levels':len(levels),'sessions':len(sessions),'attempts':len(attempts),'completed_attempts':int((attempts.result=='completed').sum()),'players_without_session':int((~players.player_id.isin(seen)).sum()),'cross_midnight_sessions':int((sessions.started_at.str[:10]!=sessions.ended_at.str[:10]).sum()),'foreign_key_errors':0,'overlapping_sessions':0,'invalid_attempts':0,'locked_level_errors':0}
    return pd.DataFrame([{'metric':k,'value':v,'scope':'full simulated database'} for k,v in info.items()])
