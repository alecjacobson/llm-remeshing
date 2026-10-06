import concurrent.futures,json,pathlib,subprocess,time,os
R=pathlib.Path(__file__).resolve().parents[1];rows=json.loads((R/'data/sample.json').read_text())['meshes'];B=os.environ.get('BLENDER_BIN','/opt/felt-monster/blender-4.5.3-linux-x64/blender')
def work(row):
 id=row['id']
 if (R/f'gallery/images/{id}_source.png').exists():return
 with open(R/f'logs/{id}.render.log','w') as log:
  p=subprocess.run([B,'-b','-t','8','--python',str(R/'scripts/make_blend.py'),'--',str(id)],stdout=log,stderr=subprocess.STDOUT)
 print('RENDERED',id,p.returncode,flush=True)
remaining={r['id']:r for r in rows if not (R/f"gallery/images/{r['id']}_source.png").exists()};active={}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 while remaining or active:
  for id,row in list(remaining.items()):
   if len(active)>=2:break
   if (R/f'results/{id}/report.json').exists():active[id]=pool.submit(work,row);del remaining[id]
  for id,f in list(active.items()):
   if f.done():f.result();del active[id]
  if not active and not any((R/f'results/{id}/report.json').exists() for id in remaining) and (R/'logs/processing.log').exists() and 'FINISHED' in (R/'logs/processing.log').read_text():
   print('WAITING_FOR_FAILED',list(remaining),flush=True);break
  time.sleep(3)
print('RENDER_BATCH_COMPLETE',flush=True)
