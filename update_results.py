#!/usr/bin/env python3
"""Nightly VFL results updater - runs at 23:55 WAT, fetches today's results, commits to GitHub."""
import urllib.request, json, datetime, os, subprocess, sys

WAT = datetime.timezone(datetime.timedelta(hours=1))
now = datetime.datetime.now(WAT)
date_str = now.strftime('%Y-%m-%d')

LEAGUES = {
    'germany': {'categoryId': 'sv:category:202120004', 'tournamentId': 'sv:league:4'},
    'spain':   {'categoryId': 'sv:category:202120002', 'tournamentId': 'sv:league:2'},
    'italy':   {'categoryId': 'sv:category:202120003', 'tournamentId': 'sv:league:3'},
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.sportybet.com/ng/sport/vfootball',
}

SPORT_ID = 'sr:sport:202120001'

def fetch_day(cat, tourn, date):
    ts = int(datetime.datetime.now(WAT).timestamp() * 1000)
    url = (f"https://www.sportybet.com/api/ng/factsCenter/eventResultList"
           f"?sportId={SPORT_ID}&categoryId={cat}&tournamentId={tourn}&date={date}&_t={ts}")
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

def events_to_txt(events, league_name, date):
    WAT = datetime.timezone(datetime.timedelta(hours=1))
    lines = [f"D?? RESULTS  -  {league_name}  -  {date} (WAT)",
             "=" * 54, ""]
    # Group by slot (42-min buckets)
    slots = {}
    for ev in events:
        ms = ev.get('estimateStartTime', 0)
        dt = datetime.datetime.fromtimestamp(ms/1000, tz=WAT)
        total_mins = dt.hour * 60 + dt.minute
        bucket = (total_mins // 42) * 42
        key = f"{bucket//60:02d}:{bucket%60:02d}"
        slots.setdefault(key, []).append((dt, ev))
    for slot_time in sorted(slots):
        for dt, ev in sorted(slots[slot_time], key=lambda x: x[0]):
            t = dt.strftime('%H:%M')
            home = ev.get('homeTeamName', '???')[:4].upper()
            away = ev.get('awayTeamName', '???')[:4].upper()
            score = ev.get('setScore', '0:0')
            lines.append(f"{t}  {home:<5} {score}  {away}")
        lines.append("")
    # Stats
    totals = [sum(int(x) for x in ev.get('setScore','0:0').split(':')) for ev in events
              if ':' in ev.get('setScore','0:0')]
    o15 = sum(1 for t in totals if t > 1)
    o25 = sum(1 for t in totals if t > 2)
    n = len(totals)
    lines += ["=" * 54,
              f"Total: {n}  |  Over 1.5: {o15}  |  Rate: {int(o15/n*100) if n else 0}%"]
    return "\n".join(lines)

def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        print(f"CMD FAILED: {cmd}\n{result.stderr}")
    return result.stdout.strip()

repo_dir = os.path.expanduser("~/onimix-vfl-engine")

def main():
    print(f"[{now.strftime('%Y-%m-%d %H:%M WAT')}] Starting nightly update...")
    fetched = 0
    for league, ids in LEAGUES.items():
        try:
            data = fetch_day(ids['categoryId'], ids['tournamentId'], date_str)
            if data.get('bizCode') == 0 and data.get('data'):
                events = data['data'].get('events', [])
                if events:
                    txt = events_to_txt(events, f"{league.capitalize()} VFL", date_str)
                    # Determine day number from file count
                    data_dir = os.path.join(repo_dir, 'data', league)
                    os.makedirs(data_dir, exist_ok=True)
                    existing = [f for f in os.listdir(data_dir) if f.endswith('.txt')]
                    day_num = len(existing) + 1
                    fname = os.path.join(data_dir, f"D{day_num:02d}.txt")
                    # Replace D?? with actual day number
                    txt = txt.replace("D??", f"D{day_num:02d}")
                    with open(fname, 'w') as f:
                        f.write(txt)
                    print(f"  {league}: {len(events)} events -> {fname}")
                    fetched += 1
                else:
                    print(f"  {league}: 0 events returned")
            else:
                print(f"  {league}: API error bizCode={data.get('bizCode')}")
        except Exception as e:
            print(f"  {league}: FETCH ERROR {e}")

    if fetched == 0:
        print("No data fetched - skipping commit")
        return

    # Fix remote URL with token
    fix_remote()
    # Git commit and push
    run(f"git -C {repo_dir} add data/", cwd=repo_dir)
    msg = f"auto: results {date_str}"
    run(f'git -C {repo_dir} commit -m "{msg}"', cwd=repo_dir)
    run(f"git -C {repo_dir} push origin main", cwd=repo_dir)
    print(f"Pushed: {msg}")

if __name__ == '__main__':
    main()

# Fix remote URL to use token (called at start)
def fix_remote():
    import os
    token = os.environ.get('GH_TOKEN', '')
    if token:
        run(f"git -C {repo_dir} remote set-url origin https://{token}@github.com/Onimix/onimix-vfl-engine.git")
