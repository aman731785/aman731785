"""Generate public GitHub analytics and an isometric calendar using GitHub GraphQL."""
import argparse, datetime as dt, json, os, urllib.request
from pathlib import Path
from collections import Counter
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[1]/'assets'
QUERY='''query($login:String!, $after:String){user(login:$login){repositories(first:100,after:$after,privacy:PUBLIC,ownerAffiliations:[OWNER],orderBy:{field:PUSHED_AT,direction:DESC}){totalCount pageInfo{hasNextPage endCursor} nodes{name stargazerCount pushedAt languages(first:100){edges{size node{name}}}}} contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount weekday}}}}}}'''
def fetch(login):
 token=os.environ['GITHUB_TOKEN']; after=None; repos=[]
 while True:
  req=urllib.request.Request('https://api.github.com/graphql',data=json.dumps({'query':QUERY,'variables':{'login':login,'after':after}}).encode(),headers={'Authorization':f'Bearer {token}','Content-Type':'application/json','User-Agent':'profile-analytics'})
  with urllib.request.urlopen(req,timeout=40) as r: data=json.load(r)
  if data.get('errors'): raise RuntimeError('GitHub GraphQL query failed')
  u=data['data']['user']; rs=u['repositories']; repos.extend(rs['nodes']); calendar=u['contributionsCollection']['contributionCalendar']
  if not rs['pageInfo']['hasNextPage']: return repos,calendar
  after=rs['pageInfo']['endCursor']
def txt(x,y,s,size=20,color='#F8FAFC',anchor='start'):
 return f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,sans-serif" font-size="{size}" text-anchor="{anchor}">{escape(str(s))}</text>'
def save(name,h,title,b):
 ROOT.mkdir(exist_ok=True); (ROOT/name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 {h}" width="1200" height="{h}" role="img"><title>{escape(title)}</title><rect width="1200" height="{h}" rx="18" fill="#020617"/>{b}</svg>')
def streak(days):
 run=best=0
 for d in days:
  run=run+1 if d['contributionCount'] else 0; best=max(best,run)
 return best
def render_stats(repos,cal):
 days=sorted([d for w in cal['weeks'] for d in w['contributionDays']],key=lambda d:d['date']); langs=Counter()
 for r in repos:
  for e in r['languages']['edges']: langs[e['node']['name']]+=e['size']
 b=txt(40,55,'GITHUB / PUBLIC ENGINEERING ACTIVITY',32,'#00E5FF')+txt(40,85,'GitHub API • contribution calendar window • repository language bytes',18,'#94A3B8')
 for i,(label,value) in enumerate([('Contributions',cal['totalContributions']),('Public repositories',len(repos)),('Repository stars',sum(r['stargazerCount'] for r in repos)),('Longest streak (days)',streak(days))]):
  x=40+i*285;b+=f'<rect x="{x}" y="110" width="265" height="105" rx="12" fill="#111827" stroke="#1E293B"/>'+txt(x+15,140,label,18,'#94A3B8')+txt(x+15,190,value,37,'#00E5FF')
 b+=txt(40,260,'LANGUAGES BY REPOSITORY BYTES',20,'#A855F7')+txt(620,260,'RECENT REPOSITORY PUSHES',20,'#A855F7')
 total=sum(langs.values())
 for i,(l,n) in enumerate(langs.most_common(5)):
  y=295+i*33; b+=txt(40,y,l,17)+f'<rect x="210" y="{y-13}" width="{300*n/total:.2f}" height="12" rx="4" fill="#2563EB"/>'+txt(560,y,f'{n/total:.1%}',16,'#94A3B8','end')
 for i,r in enumerate(repos[:5]): b+=txt(620,295+i*33,r['name'][:35],17)+txt(1150,295+i*33,(r['pushedAt'] or 'Unknown')[:10],16,'#94A3B8','end')
 b+=txt(40,495,'CONTRIBUTION ACTIVITY / WEEKLY',20,'#00E5FF'); counts=[sum(d['contributionCount'] for d in w['contributionDays']) for w in cal['weeks']]; peak=max(counts+[1]); peak=max(peak,1)
 for i,n in enumerate(counts):
  h=100*n/peak; b+=f'<rect x="{40+i*20}" y="{620-h:.2f}" width="14" height="{h:.2f}" fill="#00E5FF" opacity=".8"/>'
 b+=txt(40,652,'First week',15,'#94A3B8')+txt(1150,652,'Latest week',15,'#94A3B8','end');save('github-stats.svg',680,'GitHub activity analytics',b)
def render_3d(cal):
 b=txt(40,55,'CONTRIBUTION TERRAIN / ISOMETRIC',32,'#00E5FF')+txt(40,85,'Actual GitHub calendar counts • bar height capped for readability',18,'#94A3B8'); maximum=max([d['contributionCount'] for w in cal['weeks'] for d in w['contributionDays']]+[1]);maximum=max(1,maximum)
 for i,w in enumerate(cal['weeks']):
  for d in w['contributionDays']:
   j=d['weekday'];n=d['contributionCount'];x=105+i*18-j*9;y=195+i*.9+j*13;h=100*n/maximum; top='#00E5FF' if n else '#1E293B'; b+=f'<g><title>{d["date"]}: {n}</title><path d="M{x} {y-h}l9 -5 9 5 -9 5z" fill="{top}"/><path d="M{x} {y-h}l9 5v{h}l-9 -5z" fill="#2563EB"/><path d="M{x+9} {y-h+5}l9 -5v{h}l-9 5z" fill="#A855F7"/></g>'
 b+=txt(40,405,f'{cal["totalContributions"]} contributions in the GitHub calendar window',22);save('contributions-3d.svg',440,'Isometric contribution calendar',b)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['stats','3d'],required=True);p.add_argument('--login',default='AmanNishad-ic');a=p.parse_args();r,c=fetch(a.login);render_stats(r,c) if a.mode=='stats' else render_3d(c)
