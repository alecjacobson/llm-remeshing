import concurrent.futures, hashlib, json, pathlib, time, requests
root=pathlib.Path(__file__).resolve().parents[1]
sample=json.loads((root/'data/sample.json').read_text())
def download(row):
 path=root/'data/source'/f"{row['id']}.npz"
 path.parent.mkdir(parents=True,exist_ok=True)
 url=f"https://huggingface.co/datasets/Thingi10K/Thingi10K/resolve/{sample['revision']}/npz/{row['id']}.npz"
 for attempt in range(5):
  try:
   if not path.exists():
    r=requests.get(url,timeout=180); r.raise_for_status(); path.write_bytes(r.content)
   row['download']={'url':url,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
   print(row['index'],row['id'],path.stat().st_size,flush=True); return
  except Exception:
   if attempt==4: raise
   time.sleep(2**attempt)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: list(pool.map(download,sample['meshes']))
(root/'data/sample.json').write_text(json.dumps(sample,indent=2))
print('COMPLETE',sum(r['download']['bytes'] for r in sample['meshes']),flush=True)
