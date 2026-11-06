import argparse
import pandas as pd
from .db import connect,DEFAULT_DB
from .quality import validate
from .analysis import sql_tables,scope
from .analyze import export
def pages(frame):
    if frame.empty:print('Không có kết quả.');return
    for start in range(0,len(frame),20):
        print(frame.iloc[start:start+20].to_string(index=False))
        if start+20<len(frame) and input('Enter trang tiếp; q quay lại: ').strip().lower()=='q':break
def pick_player(db):
    text=input('Tên người chơi mẫu hoặc một phần tên (q quay lại): ').strip()
    if text.lower()=='q':return None
    with connect(db) as c:frame=pd.read_sql_query('SELECT player_id,name FROM players WHERE name LIKE ? ORDER BY player_id',c,params=('%'+text+'%',))
    if frame.empty:print('Không có kết quả.');return None
    page=0
    while True:
        for index,row in frame.iloc[page:page+20].iterrows():print(f'{index+1}. {row["name"]}')
        v=input('Chọn số thứ tự; n/p đổi trang; q quay lại: ').strip().lower()
        if v=='q':return None
        if v=='n':page=min(page+20,((len(frame)-1)//20)*20);continue
        if v=='p':page=max(0,page-20);continue
        if not v and len(frame)==1:return int(frame.iloc[0].player_id)
        if v.isdigit() and 1<=int(v)<=len(frame):return int(frame.iloc[int(v)-1].player_id)
        print('Chưa hợp lệ. Nhập số thứ tự danh sách, không cần nhớ mã người chơi.')
def ask_scope():
    start=input('Ngày chơi đầu từ [2026-01-01], q quay lại: ').strip()
    if start.lower()=='q':return None
    end=input('Ngày chơi đầu đến [mặc định bằng ngày quan sát]: ').strip()
    as_of=input('Ngày quan sát [2026-03-31]: ').strip()
    p=scope(start or '2026-01-01',end or None,as_of or '2026-03-31')
    return p['start'],p['end'],p['as_of']
def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default=str(DEFAULT_DB));args=p.parse_args()
    validate(args.db)
    while True:
        print('\nGAME RETENTION — DỮ LIỆU GIẢ LẬP\n1. Nguồn và chất lượng\n2. Tìm người chơi\n3. Lịch sử phiên/lượt thử\n4. Người hoạt động theo ngày\n5. Retention D1/D7/D30\n6. Tiến độ màn\n7. Xuất báo cáo\n8. Giải thích chỉ số\n0. Thoát')
        try:
            choice=input('Chọn số menu: ').strip()
            if choice=='0':return
            if choice=='1':
                with connect(args.db) as c:pages(pd.read_sql_query('SELECT * FROM metadata',c))
                pages(validate(args.db))
            elif choice in ('2','3'):
                player=pick_player(args.db)
                if player is not None:
                    with connect(args.db) as c:
                        if choice=='2':pages(pd.read_sql_query('SELECT p.name,COUNT(s.session_id) AS sessions,MIN(date(s.started_at)) AS first_play,MAX(date(s.started_at)) AS last_active FROM players p LEFT JOIN sessions s USING(player_id) WHERE p.player_id=? GROUP BY p.player_id',c,params=(player,)))
                        else:
                            pages(pd.read_sql_query('SELECT * FROM sessions WHERE player_id=? ORDER BY started_at,session_id',c,params=(player,)))
                            pages(pd.read_sql_query('SELECT a.attempt_id,s.session_id,l.name,a.started_at,a.ended_at,a.result FROM level_attempts a JOIN sessions s USING(session_id) JOIN levels l USING(level_id) WHERE s.player_id=? ORDER BY a.started_at,a.attempt_id',c,params=(player,)))
            elif choice in ('4','5','6','7'):
                selected=ask_scope()
                if selected is None:continue
                if choice=='7':export(args.db,*selected)
                else:
                    tables=sql_tables(args.db,*selected);pages(tables[{'4':'daily','5':'retention','6':'levels'}[choice]])
            elif choice=='8':print('GIẢ LẬP. Một người có nhiều phiên; hoạt động = ngày bắt đầu phiên. D7 là quay lại đúng ngày đầu +7, chỉ người đủ 7 ngày được tính mẫu số. Trống khác 0%. Chưa qua màn không có nghĩa bỏ game. Mỗi lượt thử chỉ được tính khi đã kết thúc đến mốc. Xem docs/metrics.md.')
            else:print('Nhập số 0–8; nếu đang trong danh sách thì chọn số thứ tự kết quả.')
        except (ValueError,OSError) as e:print('Không thực hiện được:',e)
        except (KeyboardInterrupt,EOFError):return
if __name__=='__main__':main()
