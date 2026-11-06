"""All fixtures and sample data are explicitly SIMULATED."""
import contextlib,copy,hashlib,io,json,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from game_lab.db import connect
from game_lab.sample import generate
from game_lab.prepare_data import create,prepare
from game_lab.quality import validate
from game_lab.analysis import compare,sql_tables,scope
from game_lab.analyze import export

def fixture():
    sessions=[]
    def session(player,start,end):sessions.append((len(sessions)+1,player,start,end));return len(sessions)
    session(1,'2026-01-01 10:00:00','2026-01-01 11:00:00')
    session(1,'2026-01-02 10:00:00','2026-01-02 11:00:00')
    session(1,'2026-01-02 19:00:00','2026-01-02 20:00:00')
    session(1,'2026-01-08 10:00:00','2026-01-08 11:00:00')
    session(1,'2026-01-31 10:00:00','2026-01-31 11:00:00')
    session(2,'2026-01-01 09:00:00','2026-01-01 10:00:00')
    session(3,'2026-01-02 10:00:00','2026-01-02 11:00:00')
    session(3,'2026-01-03 10:00:00','2026-01-03 11:00:00')
    session(3,'2026-01-10 10:00:00','2026-01-10 11:00:00') # D8, not D7
    session(4,'2026-03-30 10:00:00','2026-03-30 11:00:00')
    session(5,'2026-03-31 23:58:00','2026-03-31 23:59:00')
    session(6,'2026-01-01 23:50:00','2026-01-02 00:10:00')
    attempts=[(1,1,1,'2026-01-01 10:01:00','2026-01-01 10:02:00','failed'),
              (2,1,1,'2026-01-01 10:03:00','2026-01-01 10:04:00','completed'),
              (3,1,2,'2026-01-01 10:05:00','2026-01-01 10:06:00','completed'),
              (4,1,1,'2026-01-01 10:07:00','2026-01-01 10:08:00','completed'),
              (5,6,1,'2026-01-01 09:01:00','2026-01-01 09:02:00','failed'),
              (6,12,1,'2026-01-01 23:55:00','2026-01-02 00:05:00','completed')]
    return {'players':[(i,f'Mẫu {i}') for i in range(1,7)],'levels':[(i,f'Màn {i}',i) for i in range(1,11)],'sessions':sessions,'level_attempts':attempts}

class Lab(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.db=self.root/'game.db';create(self.db,data=fixture())
    def tearDown(self):self.tmp.cleanup()
    def t(self,**kw):return compare(self.db,**kw)
    def invalid(self,change):
        data=fixture();change(data)
        target=self.root/'invalid.db'
        with self.assertRaises((ValueError,sqlite3.IntegrityError)):create(target,data=data)
        self.assertFalse(target.exists())
    def test_independent_all_tables(self):self.assertEqual(set(self.t()),{'player_days','daily','retention','cohorts','levels','quality'})
    def test_multiple_sessions_one_activity(self):
        a=self.t()['player_days'];r=a[(a.player_id==1)&(a.activity_date=='2026-01-02')].iloc[0];self.assertEqual(r.session_count,2);self.assertEqual(len(a[(a.player_id==1)&(a.activity_date=='2026-01-02')]),1)
    def test_distinct_daily(self):
        d=self.t()['daily'].set_index('activity_date');self.assertEqual(d.loc['2026-01-02','active_players'],2);self.assertEqual(d.loc['2026-01-02','session_count'],3)
    def test_exact_d7(self):
        r=self.t()['retention'].set_index('day_offset');self.assertEqual(r.loc[7,'returned_players'],1);self.assertEqual(r.loc[7,'eligible_players'],4)
    def test_d8_not_d7(self):
        c=self.t()['cohorts'];self.assertEqual(c[(c.cohort_date=='2026-01-02')&(c.day_offset==7)].returned_players.iloc[0],0);self.assertEqual(c[(c.cohort_date=='2026-01-02')&(c.day_offset==8)].returned_players.iloc[0],1)
    def test_d30(self):self.assertEqual(self.t()['retention'].set_index('day_offset').loc[30,'returned_players'],1)
    def test_march31_no_d1(self):
        c=self.t()['cohorts'];r=c[(c.cohort_date=='2026-03-31')&(c.day_offset==1)].iloc[0];self.assertEqual(r.eligible_players,0);self.assertTrue(pd.isna(r.retention_pct));self.assertTrue(pd.isna(r.returned_players))
    def test_observed_zero_not_null(self):
        c=self.t()['cohorts'];r=c[(c.cohort_date=='2026-03-30')&(c.day_offset==1)].iloc[0];self.assertEqual(r.retention_pct,0)
    def test_d0_all_100(self):
        c=self.t()['cohorts'];self.assertTrue((c[c.day_offset==0].retention_pct==100).all())
    def test_mature_six_seven(self):
        a=self.t(as_of='2026-01-07')['retention'].set_index('day_offset');b=self.t(as_of='2026-01-08')['retention'].set_index('day_offset');self.assertEqual(a.loc[7,'eligible_players'],0);self.assertEqual(b.loc[7,'eligible_players'],3)
    def test_mature_29_30(self):
        a=self.t(as_of='2026-01-30')['retention'].set_index('day_offset');b=self.t(as_of='2026-01-31')['retention'].set_index('day_offset');self.assertEqual(a.loc[30,'eligible_players'],0);self.assertEqual(b.loc[30,'eligible_players'],3)
    def test_total_weighted(self):
        t=self.t();r=t['retention'].set_index('day_offset').loc[1];self.assertAlmostEqual(r.retention_pct,2/5*100);c=t['cohorts'];eligible=c[(c.day_offset==1)&(c.eligible_players>0)];self.assertNotAlmostEqual(r.retention_pct,eligible.retention_pct.mean())
    def test_end_selects_cohort_not_activity(self):
        a=self.t(end='2026-01-01')['player_days'];self.assertTrue((a.activity_date=='2026-01-31').any());self.assertNotIn(3,set(a.player_id))
    def test_first_date_before_start_filter(self):
        a=self.t(start='2026-01-02',end='2026-01-02')['player_days'];self.assertEqual(set(a.player_id),{3})
    def test_history_excludes_future_players(self):self.assertEqual(set(self.t(as_of='2026-01-01')['player_days'].player_id),{1,2,6})
    def test_cross_midnight_only_start_day(self):self.assertEqual(list(self.t()['player_days'].query('player_id==6').activity_date),['2026-01-01'])
    def test_session_capped_historical(self):
        a=self.t(as_of='2026-01-01')['player_days'];self.assertEqual(a.query('player_id==6').session_seconds.iloc[0],599)
    def test_completed_after_cutoff_invisible(self):
        a=self.t(as_of='2026-01-01')['levels'].set_index('level_id');b=self.t(as_of='2026-01-02')['levels'].set_index('level_id');self.assertEqual(a.loc[1,'completed_players'],1);self.assertEqual(b.loc[1,'completed_players'],2)
    def test_retries_not_players(self):
        l=self.t()['levels'].set_index('level_id').loc[1];self.assertEqual(l.attempt_count,5);self.assertEqual(l.attempted_players,3);self.assertEqual(l.completed_players,2)
    def test_median_to_first_excludes_replay(self):self.assertEqual(self.t()['levels'].set_index('level_id').loc[1,'median_attempts_to_first_complete'],1.5)
    def test_unattempted_level_null(self):
        l=self.t()['levels'].set_index('level_id').loc[10];self.assertEqual(l.attempted_players,0);self.assertTrue(pd.isna(l.completion_pct))
    def test_missing_days_zero(self):self.assertEqual(self.t()['daily'].set_index('activity_date').loc['2026-01-06','active_players'],0)
    def test_no_future_calendar(self):self.assertEqual(self.t(as_of='2026-01-10')['daily'].activity_date.max(),'2026-01-10')
    def test_bad_ranges(self):
        for a,b,c in [('2026-01-02','2026-01-01','2026-03-31'),('2026-01-01','2026-03-31','2026-01-31'),('2025-12-31','2026-01-01','2026-03-31'),('2026-01-01','2026-01-01','2026-04-01'),('2026-1-1','2026-01-01','2026-03-31')]:
            with self.subTest(start=a,end=b,asof=c),self.assertRaises(ValueError):scope(a,b,c)
    def test_readonly(self):
        with connect(self.db) as c,self.assertRaises(sqlite3.OperationalError):c.execute('DELETE FROM sessions')
    def test_fk_enabled(self):
        with connect(self.db,False) as c,self.assertRaises(sqlite3.IntegrityError):c.execute("INSERT INTO sessions VALUES(99,999,'2026-01-01 01:00:00','2026-01-01 02:00:00')")
    def test_duplicate_session(self):self.invalid(lambda d:d['sessions'].append(d['sessions'][0]))
    def test_missing_player(self):self.invalid(lambda d:d['sessions'].append((99,999,'2026-01-01 01:00:00','2026-01-01 02:00:00')))
    def test_wrong_time_format(self):self.invalid(lambda d:d['sessions'].append((99,2,'2026-01-03 1:00:00','2026-01-03 02:00:00')))
    def test_impossible_date(self):self.invalid(lambda d:d['sessions'].append((99,2,'2026-02-30 01:00:00','2026-02-30 02:00:00')))
    def test_nonpositive_session(self):self.invalid(lambda d:d['sessions'].append((99,2,'2026-01-03 01:00:00','2026-01-03 01:00:00')))
    def test_future_session(self):self.invalid(lambda d:d['sessions'].append((99,2,'2026-04-01 01:00:00','2026-04-01 02:00:00')))
    def test_overlapping_sessions(self):self.invalid(lambda d:d['sessions'].append((99,1,'2026-01-01 10:30:00','2026-01-01 11:30:00')))
    def test_adjacent_sessions_valid(self):
        data=fixture();data['sessions'].append((99,1,'2026-01-01 11:00:00','2026-01-01 12:00:00'));create(self.root/'adjacent.db',data=data)
    def test_attempt_outside_session(self):self.invalid(lambda d:d['level_attempts'].append((99,1,1,'2026-01-01 11:00:00','2026-01-01 11:10:00','failed')))
    def test_attempt_overlap(self):self.invalid(lambda d:d['level_attempts'].append((99,1,1,'2026-01-01 10:01:30','2026-01-01 10:03:00','failed')))
    def test_locked_level(self):self.invalid(lambda d:d['level_attempts'].append((99,6,2,'2026-01-01 09:03:00','2026-01-01 09:04:00','failed')))
    def test_invalid_result(self):self.invalid(lambda d:d['level_attempts'].append((99,1,1,'2026-01-01 10:20:00','2026-01-01 10:21:00','unknown')))
    def test_missing_level(self):self.invalid(lambda d:d['level_attempts'].append((99,1,999,'2026-01-01 10:20:00','2026-01-01 10:21:00','failed')))
    def test_no_overwrite(self):
        before=self.db.read_bytes()
        with self.assertRaises(FileExistsError):create(self.db)
        self.assertEqual(self.db.read_bytes(),before)
    def test_prepare_preserves_and_exports(self):
        before=self.db.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):prepare(self.db,self.root/'raw')
        self.assertEqual(self.db.read_bytes(),before);self.assertEqual(len(list((self.root/'raw').glob('*.csv'))),5)
    def test_atomic_publish_failure(self):
        target=self.root/'failed.db'
        with patch('game_lab.prepare_data.os.link',side_effect=OSError('simulated failure')),self.assertRaises(OSError):create(target,data=fixture())
        self.assertFalse(target.exists());self.assertEqual(list(self.root.glob('tmp*.db')),[])
    def test_empty_cohort_outputs(self):
        t=export(self.db,'2026-02-01','2026-02-02',out=self.root/'out');self.assertEqual(t['daily'].active_players.sum(),0);self.assertTrue(t['retention'].retention_pct.isna().all());self.assertEqual(len(list((self.root/'out').glob('*.png'))),4);self.assertEqual(len(list((self.root/'out').glob('*.csv'))),6)
    def test_failure_before_report(self):
        with connect(self.db,False) as c:c.execute("UPDATE metadata SET value='real' WHERE key='data_kind'")
        with self.assertRaises(ValueError):export(self.db,out=self.root/'out')
        self.assertFalse((self.root/'out').exists())
    def test_no_attempts_database(self):
        data=fixture();data['level_attempts']=[];target=self.root/'none.db';create(target,data=data);t=compare(target);self.assertEqual(t['levels'].attempt_count.sum(),0)
    def test_empty_database(self):
        data=fixture();data['level_attempts']=[];data['sessions']=[];data['players']=[];target=self.root/'empty.db';create(target,data=data);t=compare(target);self.assertEqual(t['daily'].active_players.sum(),0)
    def test_menu_retry(self):
        from game_lab.cli import pick_player
        with patch('builtins.input',side_effect=['Mẫu 1','bad','999','1']),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(pick_player(self.db),1)
    def test_menu_quit(self):
        from game_lab.cli import pick_player
        with patch('builtins.input',return_value='q'):self.assertIsNone(pick_player(self.db))
    def test_transaction_rolls_back(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with connect(self.db,False) as c:
                c.execute("INSERT INTO players VALUES(99,'Mẫu thêm')")
                c.execute("INSERT INTO sessions VALUES(99,999,'2026-01-01 01:00:00','2026-01-01 02:00:00')")
        with connect(self.db) as c:self.assertIsNone(c.execute('SELECT * FROM players WHERE player_id=99').fetchone())

class Reproducibility(unittest.TestCase):
    def test_seed_reproducible(self):self.assertEqual(generate(),generate())
    def test_seed_changes(self):self.assertNotEqual(generate(42)['sessions'][:10],generate(43)['sessions'][:10])
    def test_sample_all_cases(self):
        data=generate();self.assertEqual(len(data['players']),3000);self.assertEqual(len(data['levels']),10);self.assertEqual(len(data['sessions']),24837);self.assertEqual(len(data['level_attempts']),52274)
        attempted={a[1] for a in data['level_attempts']};self.assertTrue(any(s[0] not in attempted for s in data['sessions']));self.assertTrue(any(s[2][:10]!=s[3][:10] for s in data['sessions']))

if __name__=='__main__':unittest.main()
