"""Reproducible SIMULATED game histories, never claims about a real game."""
import random
from datetime import datetime,timedelta
START=datetime(2026,1,1);END=datetime(2026,3,31,23,59,59)
def generate(seed=42):
    rng=random.Random(seed);players=[];sessions=[];attempts=[]
    levels=[(i,f'Màn giả lập {i:02d}',i) for i in range(1,11)]
    for player in range(1,3001):
        players.append((player,f'Người chơi mẫu {player:04d}'))
        first=0 if player==1 else 89 if player==3000 else rng.randrange(90)
        style=rng.random();active=[first]
        if player==1:active=list(range(0,90,3))
        elif style>.22:
            chance=.06+style*.32
            active.extend(d for d in range(first+1,90) if rng.random()<chance/(1+(d-first)/45))
        highest=0
        for day in active:
            count=2 if rng.random()<.23 else 1
            for slot in range(count):
                cross=count==1 and day<89 and rng.random()<.04
                hour=23 if cross else (9 if slot==0 else 19)
                minute=45 if cross else rng.randrange(40)
                begin=START+timedelta(days=day,hours=hour,minutes=minute)
                finish=min(begin+timedelta(minutes=rng.randint(20,55)),END)
                sid=len(sessions)+1;sessions.append((sid,player,begin.strftime('%Y-%m-%d %H:%M:%S'),finish.strftime('%Y-%m-%d %H:%M:%S')))
                cursor=begin+timedelta(minutes=1)
                for _ in range(rng.randint(1,4) if rng.random()>.16 else 0):
                    level=rng.randint(1,highest) if highest and (highest==10 or rng.random()<.12) else highest+1
                    stop=cursor+timedelta(minutes=rng.randint(2,5))
                    if stop>finish:break
                    passed=player==1 or rng.random()<max(.2,.86-level*.045)
                    result='completed' if passed else 'failed'
                    attempts.append((len(attempts)+1,sid,level,cursor.strftime('%Y-%m-%d %H:%M:%S'),stop.strftime('%Y-%m-%d %H:%M:%S'),result))
                    if passed:highest=max(highest,level)
                    cursor=stop+timedelta(seconds=30)
    return {'players':players,'levels':levels,'sessions':sessions,'level_attempts':attempts}
