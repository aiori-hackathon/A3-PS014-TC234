#!/usr/bin/env python3
"""NetCompare volunteer endpoint agent. See README before enabling collection."""
import os, sys, time, json, socket, platform, subprocess, statistics, argparse
from datetime import datetime, timezone
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv
load_dotenv()
API=os.getenv('API_URL','http://localhost:4000').rstrip('/')
TOKEN=os.getenv('AGENT_TOKEN','')
PARTICIPANT=os.getenv('PARTICIPANT_ID','')
MEDIUM=os.getenv('ACCESS_MEDIUM','FIBER')
ISP=os.getenv('ISP_LABEL','unknown')
LOCATION=os.getenv('LOCATION_LABEL','participant-area')
CONNECTION=os.getenv('CONNECTION_TYPE','WIFI').upper()
TARGET=os.getenv('MEASUREMENT_TARGET','https://speed.cloudflare.com/__down?bytes=1000000')
DNS_HOST=os.getenv('DNS_HOSTNAME','example.com')
MAX_DOWN=int(os.getenv('MAX_DOWNLOAD_BYTES','1000000'))
MAX_UP=int(os.getenv('MAX_UPLOAD_BYTES','500000'))
INTERVAL=int(os.getenv('INTERVAL_SECONDS','3600'))

def resolve_dns(host):
    start=time.perf_counter(); socket.getaddrinfo(host,None); return (time.perf_counter()-start)*1000

def ping(host='1.1.1.1',count=10):
    cmd=['ping','-n' if os.name=='nt' else '-c',str(count),host]
    try:
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
        import re
        text=result.stdout+'\n'+result.stderr
        times=[float(x) for x in re.findall(r'time[=<]\s*(\d+(?:\.\d+)?)\s*ms',text,re.I)]
        sent=count; received=len(times)
        return (statistics.mean(times) if times else None,(sent-received)/sent*100,times)
    except Exception as exc:
        print('ping failed:',exc,file=sys.stderr); return None,100.0,[]

def download_mbps():
    # Keep data bounded. Do not run more often than the participant's agreed schedule.
    url=TARGET
    if 'bytes=' in url: url=url.split('bytes=')[0]+'bytes='+str(MAX_DOWN)
    start=time.perf_counter(); total=0
    with requests.get(url,stream=True,timeout=20) as response:
        response.raise_for_status()
        for block in response.iter_content(65536):
            total+=len(block)
            if total>=MAX_DOWN: break
    elapsed=max(time.perf_counter()-start,.001)
    return min(total,MAX_DOWN)*8/elapsed/1_000_000

def upload_mbps():
    # Operator must provide an authorized endpoint accepting POST /upload; avoid sending data elsewhere.
    url=os.getenv('UPLOAD_ENDPOINT')
    if not url: return None
    payload=b'0'*MAX_UP; start=time.perf_counter()
    response=requests.post(url,data=payload,headers={'Content-Type':'application/octet-stream'},timeout=30)
    response.raise_for_status(); return len(payload)*8/max(time.perf_counter()-start,.001)/1_000_000

def collect():
    host=urlparse(TARGET).hostname or '1.1.1.1'
    latency,loss,samples=ping(host)
    try: dns=resolve_dns(DNS_HOST)
    except Exception: dns=None
    base_jitter=statistics.mean([abs(b-a) for a,b in zip(samples,samples[1:])]) if len(samples)>1 else None
    down=download_mbps()
    try: up=upload_mbps()
    except Exception as exc: print('upload failed:',exc,file=sys.stderr); up=None
    # Loaded jitter approximated using ping RTT deltas during transfer conditions; no concurrent flood traffic.
    loaded_jitter=base_jitter
    return {'participantId':PARTICIPANT,'accessMedium':MEDIUM,'isp':ISP,'locationLabel':LOCATION,'connectionType':CONNECTION,'latencyMs':latency,'packetLossPct':loss,'dnsMs':dns,'downloadMbps':down,'uploadMbps':up,'loadedJitterMs':loaded_jitter,'conditions':{'timestamp':datetime.now(timezone.utc).isoformat(),'agentVersion':'1.0.0','os':platform.platform(),'probeHost':host,'dnsHost':DNS_HOST,'pingProbes':10,'maxDownloadBytes':MAX_DOWN,'maxUploadBytes':MAX_UP,'loadedJitterMethod':'unloaded RTT variation proxy; not a controlled loaded-jitter test'},'status':'SUCCESS','source':'AGENT'}

def submit(data):
    if not TOKEN or not PARTICIPANT: raise RuntimeError('Set AGENT_TOKEN and PARTICIPANT_ID in the agent environment')
    response=requests.post(API+'/api/measurements',json=data,headers={'Authorization':'Bearer '+TOKEN},timeout=15)
    response.raise_for_status(); return response.json()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true');args=parser.parse_args()
    if not TOKEN or not PARTICIPANT: sys.exit('Set AGENT_TOKEN and PARTICIPANT_ID before running.')
    while True:
        started=time.time()
        try:
            result=collect(); result['measuredAt']=datetime.now(timezone.utc).isoformat(); print(json.dumps({'measurement':result,'submission':submit(result)},default=str))
        except Exception as exc:
            failed={'participantId':PARTICIPANT,'accessMedium':MEDIUM,'isp':ISP,'locationLabel':LOCATION,'connectionType':CONNECTION,'status':'FAILED','error':str(exc)[:450],'source':'AGENT','conditions':{'timestamp':datetime.now(timezone.utc).isoformat()}}
            try: submit(failed)
            except Exception as api_exc: print('collection/submission failed:',exc,'; API:',api_exc,file=sys.stderr)
        if args.once: return
        time.sleep(max(1,INTERVAL-(time.time()-started)))
if __name__=='__main__': main()
