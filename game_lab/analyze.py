import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from .db import ROOT,DEFAULT_DB
from .analysis import compare,scope
def export(db=DEFAULT_DB,start='2026-01-01',end=None,as_of='2026-03-31',out=None):
    p=scope(start,end,as_of);tables=compare(db,start,end,as_of)
    out=Path(out or ROOT/'outputs');out.mkdir(parents=True,exist_ok=True)
    for name,frame in tables.items():frame.to_csv(out/(name+'.csv'),index=False,encoding='utf-8-sig')
    sns.set_theme(style='whitegrid');foot=f'SIMULATED seed 42 | First-play cohort: {p["start"]} to {p["end"]} | As of {as_of}, Asia/Ho_Chi_Minh'
    def save(name,draw,empty=False,size=(11,6)):
        fig,ax=plt.subplots(figsize=size)
        if empty:ax.text(.5,.5,'No eligible observations',ha='center',transform=ax.transAxes);ax.set_axis_off()
        else:draw(ax)
        fig.text(.02,.015,foot,fontsize=8);fig.tight_layout(rect=(0,.055,1,1));fig.savefig(out/name,dpi=140);plt.close(fig)
    d=tables['daily'];r=tables['retention'];c=tables['cohorts'];l=tables['levels']
    def daily(ax):
        view=d.copy();view['activity_date']=pd.to_datetime(view.activity_date)
        sns.lineplot(data=view,x='activity_date',y='active_players',ax=ax);ax.set(xlabel='Session start date',ylabel='Distinct active players');ax.tick_params(axis='x',rotation=30)
    save('01_daily_active.png',daily,d.active_players.sum()==0)
    def retention(ax):
        view=r.copy();view['horizon']='D'+view.day_offset.astype(str)
        sns.barplot(data=view,x='horizon',y='retention_pct',color='#268a91',ax=ax)
        ax.set(xlabel='Exact calendar day after first play',ylabel='Retention (%)',ylim=(0,105))
        for i,row in enumerate(view.itertuples()):ax.text(i,(row.retention_pct if pd.notna(row.retention_pct) else 0)+3,f'{row.returned_players}/{row.eligible_players}'+(' (not observable)' if not row.eligible_players else ''),ha='center',fontsize=9)
    save('02_retention.png',retention,r.eligible_players.sum()==0)
    def heat(ax):
        grid=c.pivot(index='cohort_date',columns='day_offset',values='retention_pct')
        sns.heatmap(grid,mask=grid.isna(),vmin=0,vmax=100,cmap='viridis',ax=ax,cbar_kws={'label':'Exact-day retention (%)'},yticklabels=max(1,len(grid)//18))
        ax.set_facecolor('#eeeeee');ax.set(xlabel='Days since first play (blank = not observable)',ylabel='First-play cohort date')
    save('03_cohort_heatmap.png',heat,c.empty,size=(13,8))
    def levels(ax):
        view=l.melt(id_vars=['name'],value_vars=['attempted_players','completed_players'],var_name='measure',value_name='players')
        sns.barplot(data=view,x='name',y='players',hue='measure',ax=ax);ax.set(xlabel='SIMULATED sequential level',ylabel='Distinct players');ax.tick_params(axis='x',rotation=30)
    save('04_level_progress.png',levels,l.attempt_count.sum()==0)
    n=tables['player_days'].player_id.nunique();sessions=int(d.session_count.sum());seconds=int(d.session_seconds.sum())
    insights=[f'Nhóm có {n:,} người, {sessions:,} phiên và {seconds/3600:,.2f} giờ phiên ghi nhận đến mốc. Phiên qua đêm tính hoạt động theo ngày bắt đầu.']
    insights.append('Retention đúng ngày: '+'; '.join(f'D{row.day_offset}: {row.returned_players}/{row.eligible_players} = {row.retention_pct:.2f}%' if row.eligible_players else f'D{row.day_offset}: chưa có mẫu đủ thời gian' for row in r.itertuples())+'. Mẫu số từng mốc có thể khác nhau.')
    used=l[l.attempted_players>0]
    if len(used):
        most=used.sort_values(['not_completed_players','level_order'],ascending=[False,True]).iloc[0]
        insights.append(f'{most["name"]}: {int(most.not_completed_players):,}/{int(most.attempted_players):,} người đã thử nhưng chưa hoàn thành đến mốc; không đồng nghĩa bỏ game.')
    else:insights.append('Chưa có lượt thử hoàn thành quan sát được trong nhóm; không suy tỷ lệ qua màn.')
    text='# Game Retention Analytics — GIẢ LẬP\n\n'+foot+'\n\n'+'\n\n'.join(f'{i}. {s}' for i,s in enumerate(insights,1))
    text+='\n\n## Định nghĩa và giới hạn\n\nNgày hoạt động là ngày bắt đầu phiên, không tự tạo ngày mới khi phiên qua nửa đêm. Retention là quay lại đúng ngày lịch Dn; chỉ dùng người đủ thời gian quan sát. Heatmap trống = chưa quan sát được; 0% = đã đủ thời gian nhưng không quay lại. D0 của nhóm có người luôn bằng 100%.\n\nLượt thử tính khi đã kết thúc đến mốc. Trung vị lượt thử đến lần hoàn thành đầu chỉ dùng người đã hoàn thành, không mô tả người chưa qua màn. Thời lượng phiên được cắt tại mốc lịch sử, không phải toàn bộ thời gian thao tác tích cực. Chưa hoàn thành không chứng minh rời bỏ game; không kết luận màn gây bỏ cuộc.\n\nSQL/pandas đã đối chiếu độc lập từ bảng nguồn. quality.csv kiểm tra toàn database; năm bảng còn lại theo nhóm và mốc đã chọn. Dữ liệu giả lập seed 42, không đại diện game thật hoặc đánh giá người chơi thật.\n'
    (out/'report.md').write_text(text,encoding='utf-8');print('GIẢ LẬP: SQL/pandas khớp; đã xuất 4 PNG, 6 CSV, report.md:',out)
    return tables
def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default=str(DEFAULT_DB));p.add_argument('--start',default='2026-01-01');p.add_argument('--end');p.add_argument('--as-of',default='2026-03-31');p.add_argument('--out');a=p.parse_args();export(a.db,a.start,a.end,a.as_of,a.out)
if __name__=='__main__':main()
