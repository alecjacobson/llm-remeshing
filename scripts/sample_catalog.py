"""Select IDs before downloading geometry. Never initializes the full dataset."""
import argparse,hashlib,json,pathlib,random,secrets,csv,requests
R=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--seed',type=int);p.add_argument('--count',type=int,default=100);p.add_argument('--verify',action='store_true');args=p.parse_args()
manifest=R/'data/sample.json'
if manifest.exists():
 old=json.loads(manifest.read_text());seed=old['seed'] if args.seed is None else args.seed;revision=old['revision']
else:
 old=None;seed=args.seed if args.seed is not None else secrets.randbits(64);revision=requests.get('https://huggingface.co/api/datasets/Thingi10K/Thingi10K',timeout=30).json()['sha']
for name in ['input_summary.csv','contextual_data.csv','geometry_data.csv']:
 path=R/'data/metadata'/name;path.parent.mkdir(exist_ok=True,parents=True)
 if not path.exists():
  response=requests.get(f'https://huggingface.co/datasets/Thingi10K/Thingi10K/resolve/{revision}/metadata/{name}',timeout=60);response.raise_for_status();path.write_bytes(response.content)
rows=list(csv.DictReader((R/'data/metadata/input_summary.csv').open()));population=sorted(int(r['ID']) for r in rows);ids=random.Random(seed).sample(population,args.count)
if args.verify:
 assert old is not None and ids==[r['id'] for r in old['meshes']]
 assert len(ids)==len(set(ids))==args.count
 assert {int(x.stem) for x in (R/'data/source').glob('*.npz')}==set(ids)
 for r in old['meshes']:assert hashlib.sha256((R/f"data/source/{r['id']}.npz").read_bytes()).hexdigest()==r['download']['sha256']
 print(f'VERIFIED: uniform sample of {len(ids)} / {len(population)}; all 100 source hashes match; no extra mesh downloads.')
else:
 print(json.dumps({'seed':seed,'revision':revision,'population':len(population),'sampled_ids':ids},indent=2))
