#!/usr/bin/env python3
# CF Web Analytics 外部来源(近 8 天,免费版只留 7 天)。用法: ./cf_referrers.sh
import json,subprocess,sys,datetime,collections
tok=sys.argv[1]
agg=collections.Counter(); daily=collections.defaultdict(collections.Counter); pages=collections.defaultdict(collections.Counter)
today=datetime.date.today()
for i in range(7,-1,-1):
    d=today-datetime.timedelta(days=i); s=d.isoformat()+"T00:00:00Z"; e=(d+datetime.timedelta(days=1)).isoformat()+"T00:00:00Z"
    q='''{viewer{accounts(filter:{accountTag:"fef36090acf8aa09ecb47dbded9f61e7"}){rumPageloadEventsAdaptiveGroups(limit:1000,filter:{siteTag:"a46dbde2929b4ab3a118869ebd315f27",datetime_geq:"%s",datetime_lt:"%s"}){count sum{visits} dimensions{refererHost requestPath}}}}}'''%(s,e)
    # 先直连,不通再走系统代理(Clash 开关状态不同,两种都可能是唯一能通的)
    for np in (['--noproxy','*'],[]):
        r=subprocess.run(['curl','-s','-m','20',*np,'https://api.cloudflare.com/client/v4/graphql','-H','Authorization: Bearer '+tok,'-H','Content-Type: application/json','-d',json.dumps({'query':q})],capture_output=True,text=True)
        if r.stdout.strip(): break
    j=json.loads(r.stdout)
    if j.get('errors'): print(s,j['errors'][0]['message']); continue
    for g in j['data']['viewer']['accounts'][0]['rumPageloadEventsAdaptiveGroups']:
        h=g['dimensions']['refererHost'] or '(direct)'; v=g['sum']['visits']
        if h=='readmandarin.com' or v==0: continue
        agg[h]+=v; daily[d.isoformat()][h]+=v; pages[h][g['dimensions']['requestPath']]+=v
print('近8天外部来源 visits:')
for h,v in agg.most_common(): print(f'  {h:35} {v}')
print()
for d in sorted(daily): print(d, sum(daily[d].values()), dict(daily[d].most_common(6)))
print()
for h in agg:
    if any(k in h for k in ('bing','copilot','chatgpt','openai','perplexity','gemini','claude','duckduckgo','google')):
        print(h, pages[h].most_common(8))
