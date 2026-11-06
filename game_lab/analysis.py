from datetime import date,timedelta
import pandas as pd
import numpy as np
from .db import connect,day
from .quality import validate
def scope(start='2026-01-01',end=None,as_of='2026-03-31'):
    end=end or as_of
    for v in (start,end,as_of):day(v)
    if not '2026-01-01'<=start<=end<=as_of<='2026-03-31':raise ValueError('Cần 2026-01-01 <= start <= end <= as-of <= 2026-03-31')
    return {'start':start,'end':end,'as_of':as_of,'cutoff':as_of+' 23:59:59'}
BASE='''WITH observed AS (
    SELECT * FROM sessions WHERE started_at<=:cutoff
), firsts AS (
    SELECT player_id,MIN(date(started_at)) AS cohort_date FROM observed GROUP BY player_id
), selected AS (
    SELECT * FROM firsts WHERE cohort_date BETWEEN :start AND :end
), used_sessions AS (
    SELECT o.*,f.cohort_date FROM observed o JOIN selected f USING(player_id)
), player_days AS MATERIALIZED (
    SELECT player_id,cohort_date,date(started_at) AS activity_date,COUNT(*) AS session_count,
    SUM(unixepoch(MIN(ended_at,:cutoff))-unixepoch(started_at)) AS session_seconds
    FROM used_sessions GROUP BY player_id,cohort_date,date(started_at)
)'''
OVERALL=BASE+''', horizons(day_offset) AS (VALUES(1),(7),(30))
SELECT h.day_offset,COUNT(s.player_id) AS eligible_players,
    COALESCE(SUM(CASE WHEN EXISTS(SELECT 1 FROM player_days a WHERE a.player_id=s.player_id AND a.activity_date=date(s.cohort_date,'+'||h.day_offset||' days')) THEN 1 ELSE 0 END),0) AS returned_players
FROM horizons h LEFT JOIN selected s ON date(s.cohort_date,'+'||h.day_offset||' days')<=:as_of
GROUP BY h.day_offset ORDER BY h.day_offset'''
COHORT=BASE+''', offsets(day_offset) AS (SELECT 0 UNION ALL SELECT day_offset+1 FROM offsets WHERE day_offset<30), groups AS (
    SELECT cohort_date,COUNT(*) AS cohort_size FROM selected GROUP BY cohort_date
)
SELECT g.cohort_date,h.day_offset,g.cohort_size,
    CASE WHEN date(g.cohort_date,'+'||h.day_offset||' days')<=:as_of THEN g.cohort_size ELSE 0 END AS eligible_players,
    CASE WHEN date(g.cohort_date,'+'||h.day_offset||' days')<=:as_of THEN
        (SELECT COUNT(*) FROM player_days a WHERE a.cohort_date=g.cohort_date AND a.activity_date=date(g.cohort_date,'+'||h.day_offset||' days')) ELSE NULL END AS returned_players
FROM groups g CROSS JOIN offsets h ORDER BY g.cohort_date,h.day_offset'''
LEVELS=BASE+''', ranked_attempts AS (
    SELECT a.*,s.player_id,ROW_NUMBER() OVER(PARTITION BY s.player_id,a.level_id ORDER BY a.started_at,a.attempt_id) AS attempt_number
    FROM level_attempts a JOIN used_sessions s USING(session_id) WHERE a.ended_at<=:cutoff
), per_player AS (
    SELECT player_id,level_id,COUNT(*) AS attempts,
    MAX(CASE WHEN result='completed' THEN 1 ELSE 0 END) AS completed,
    MIN(CASE WHEN result='completed' THEN attempt_number END) AS attempts_to_first_complete
    FROM ranked_attempts GROUP BY player_id,level_id
), summary AS (
    SELECT level_id,COUNT(*) AS attempted_players,SUM(completed) AS completed_players,SUM(attempts) AS attempt_count
    FROM per_player GROUP BY level_id
), counts AS (
    SELECT level_id,SUM(result='completed') AS completed_attempts,SUM(result='failed') AS failed_attempts FROM ranked_attempts GROUP BY level_id
), median_ranked AS (
    SELECT level_id,attempts_to_first_complete,
    ROW_NUMBER() OVER(PARTITION BY level_id ORDER BY attempts_to_first_complete,player_id) AS rn,
    COUNT(*) OVER(PARTITION BY level_id) AS n FROM per_player WHERE completed=1
), medians AS (
    SELECT level_id,AVG(attempts_to_first_complete) AS median_attempts_to_first_complete FROM median_ranked
    WHERE rn IN ((n+1)/2,(n+2)/2) GROUP BY level_id
)
SELECT l.level_id,l.name,l.level_order,COALESCE(s.attempted_players,0) AS attempted_players,
    COALESCE(s.completed_players,0) AS completed_players,COALESCE(s.attempt_count,0) AS attempt_count,
    COALESCE(c.completed_attempts,0) AS completed_attempts,COALESCE(c.failed_attempts,0) AS failed_attempts,
    m.median_attempts_to_first_complete
FROM levels l LEFT JOIN summary s USING(level_id) LEFT JOIN counts c USING(level_id) LEFT JOIN medians m USING(level_id)
ORDER BY l.level_order'''
def rate(frame):
    frame=frame.copy();frame['retention_pct']=pd.to_numeric(frame.returned_players)/pd.to_numeric(frame.eligible_players).replace(0,np.nan)*100
    return frame
def level_rate(frame):
    frame=frame.copy();frame['not_completed_players']=frame.attempted_players-frame.completed_players
    frame['completion_pct']=frame.completed_players/frame.attempted_players.replace(0,np.nan)*100
    return frame
def daily_table(activities,params):
    grid=pd.DataFrame({'activity_date':pd.date_range(params['start'],params['as_of']).strftime('%Y-%m-%d')})
    if activities.empty:
        grid['active_players']=0;grid['session_count']=0;grid['session_seconds']=0
        return grid
    d=activities.groupby('activity_date',as_index=False).agg(active_players=('player_id','nunique'),session_count=('session_count','sum'),session_seconds=('session_seconds','sum'))
    d=grid.merge(d,on='activity_date',how='left')
    for col in ['active_players','session_count','session_seconds']:d[col]=pd.to_numeric(d[col]).fillna(0).astype('int64')
    return d
def sql_tables(db,start='2026-01-01',end=None,as_of='2026-03-31'):
    p=scope(start,end,as_of)
    with connect(db) as c:
        activity=pd.read_sql_query(BASE+' SELECT * FROM player_days ORDER BY player_id,activity_date',c,params=p)
        # Daily aggregation is SQL too, with a full calendar and a zero-day LEFT JOIN.
        daily=pd.read_sql_query(BASE+''', calendar(activity_date) AS (
            SELECT :start UNION ALL SELECT date(activity_date,'+1 day') FROM calendar WHERE activity_date<:as_of
        ), totals AS (SELECT activity_date,COUNT(*) AS active_players,SUM(session_count) AS session_count,SUM(session_seconds) AS session_seconds FROM player_days GROUP BY activity_date)
        SELECT calendar.activity_date,COALESCE(active_players,0) AS active_players,COALESCE(session_count,0) AS session_count,COALESCE(session_seconds,0) AS session_seconds
        FROM calendar LEFT JOIN totals USING(activity_date) ORDER BY calendar.activity_date''',c,params=p)
        retention=rate(pd.read_sql_query(OVERALL,c,params=p));cohorts=rate(pd.read_sql_query(COHORT,c,params=p))
        levels=level_rate(pd.read_sql_query(LEVELS,c,params=p))
    return {'player_days':activity,'daily':daily,'retention':retention,'cohorts':cohorts,'levels':levels}
def pandas_tables(db,start='2026-01-01',end=None,as_of='2026-03-31'):
    p=scope(start,end,as_of)
    with connect(db) as c:
        sessions=pd.read_sql_query('SELECT * FROM sessions',c);attempts=pd.read_sql_query('SELECT * FROM level_attempts',c);levels=pd.read_sql_query('SELECT * FROM levels ORDER BY level_order',c)
    observed=sessions[sessions.started_at<=p['cutoff']].copy()
    firsts=observed.assign(cohort_date=observed.started_at.str[:10]).groupby('player_id',as_index=False).cohort_date.min()
    selected=firsts[firsts.cohort_date.between(p['start'],p['end'])]
    used=observed.merge(selected,on='player_id',validate='many_to_one');used['activity_date']=used.started_at.str[:10]
    used['session_seconds']=[int((pd.Timestamp(min(e,p['cutoff']))-pd.Timestamp(s)).total_seconds()) for s,e in zip(used.started_at,used.ended_at)]
    activity=used.groupby(['player_id','cohort_date','activity_date'],as_index=False).agg(session_count=('session_id','size'),session_seconds=('session_seconds','sum'))
    present=set(zip(activity.player_id,activity.activity_date));overall=[];cohorts=[]
    for offset in [1,7,30]:
        eligible=selected[pd.to_datetime(selected.cohort_date)+pd.to_timedelta(offset,unit='D')<=pd.Timestamp(p['as_of'])]
        returned=sum((int(r.player_id),(date.fromisoformat(r.cohort_date)+timedelta(days=offset)).isoformat()) in present for r in eligible.itertuples())
        overall.append({'day_offset':offset,'eligible_players':len(eligible),'returned_players':returned})
    for cohort,g in selected.groupby('cohort_date'):
        for offset in range(31):
            target=(date.fromisoformat(cohort)+timedelta(days=offset)).isoformat();mature=target<=p['as_of']
            returned=sum((int(player),target) in present for player in g.player_id) if mature else None
            cohorts.append({'cohort_date':cohort,'day_offset':offset,'cohort_size':len(g),'eligible_players':len(g) if mature else 0,'returned_players':returned})
    a=attempts[(attempts.ended_at<=p['cutoff'])].merge(used[['session_id','player_id']],on='session_id',validate='many_to_one').sort_values(['player_id','level_id','started_at','attempt_id'])
    a['attempt_number']=a.groupby(['player_id','level_id']).cumcount()+1
    summary=[]
    for level in levels.itertuples(index=False):
        g=a[a.level_id==level.level_id];completed=g[g.result=='completed'];first_complete=completed.groupby('player_id').attempt_number.min()
        summary.append({'level_id':level.level_id,'name':level.name,'level_order':level.level_order,'attempted_players':g.player_id.nunique(),'completed_players':completed.player_id.nunique(),'attempt_count':len(g),'completed_attempts':len(completed),'failed_attempts':int((g.result=='failed').sum()),'median_attempts_to_first_complete':first_complete.median() if len(first_complete) else np.nan})
    return {'player_days':activity,'daily':daily_table(activity,p),'retention':rate(pd.DataFrame(overall)),'cohorts':rate(pd.DataFrame(cohorts,columns=['cohort_date','day_offset','cohort_size','eligible_players','returned_players'])),'levels':level_rate(pd.DataFrame(summary,columns=['level_id','name','level_order','attempted_players','completed_players','attempt_count','completed_attempts','failed_attempts','median_attempts_to_first_complete']))}
def compare(db,start='2026-01-01',end=None,as_of='2026-03-31'):
    q=validate(db);sql=sql_tables(db,start,end,as_of);pan=pandas_tables(db,start,end,as_of)
    keys={'player_days':['player_id','activity_date'],'daily':['activity_date'],'retention':['day_offset'],'cohorts':['cohort_date','day_offset'],'levels':['level_order']}
    for name,sort in keys.items():
        a=sql[name].sort_values(sort).reset_index(drop=True);b=pan[name].reindex(columns=a.columns).sort_values(sort).reset_index(drop=True)
        if a.shape!=b.shape:raise ValueError('SQL/pandas khác số dòng: '+name)
        for col in a:
            if col in ('retention_pct','completion_pct','median_attempts_to_first_complete'):
                if not np.allclose(pd.to_numeric(a[col]).astype(float),pd.to_numeric(b[col]).astype(float),rtol=0,atol=1e-8,equal_nan=True):raise ValueError('SQL/pandas khác: '+name+'.'+col)
            elif not ((a[col]==b[col])|(a[col].isna()&b[col].isna())).all():raise ValueError('SQL/pandas khác: '+name+'.'+col)
    sql['quality']=q;return sql
