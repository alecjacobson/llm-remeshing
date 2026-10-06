import concurrent.futures,json,pathlib,subprocess,sys,time,os
R=pathlib.Path(__file__).resolve().parents[1]; rows=json.loads((R/'data/sample.json').read_text())['meshes']
def work(pair):
 k,row=pair;id=row['id']
 if (R/f'results/{id}/report.json').exists():return id,0
 with open(R/f'logs/{id}.process.log','w') as log:
  p=subprocess.run(['taskset','-c',f'{24+(k%6)*8}-{31+(k%6)*8}',sys.executable,str(R/'scripts/process_mesh.py'),str(id)],stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'4'})
 print('PROCESSED',id,p.returncode,flush=True);return id,p.returncode
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 results=list(pool.map(work,enumerate(rows)))
print('FINISHED',results,flush=True)
