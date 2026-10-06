import json,pathlib,html,csv
R=pathlib.Path(__file__).resolve().parents[1];s=json.loads((R/'data/sample.json').read_text());data=[]
for row in s['meshes']:
 p=R/f"results/{row['id']}/report.json"
 if not p.exists():continue
 r=json.loads(p.read_text())
 review=p.parent/'deviation_review.json'
 if review.exists():r['deviation_review']=json.loads(review.read_text())
 r.update(name=html.unescape(row['context']['Name']).strip(),author=row['context']['Author'],license=row['context']['License'],thing_id=row['source']['Thing ID']);data.append(r)
info={'seed':str(s['seed']),'population':s['population'],'revision':s['revision'],'bytes':sum(r['download']['bytes'] for r in s['meshes'])}
(R/'gallery/index.html').write_text((R/'gallery/template.html').read_text().replace('__DATA__',json.dumps(data).replace('</','<\\/')).replace('__SAMPLE__',json.dumps(info)))
summary={'completed':len(data),'exact_surface_count':sum(r['exact_source_surface'] for r in data),'reconstructed_count':sum(not r['exact_source_surface'] for r in data),'all_watertight':all(r['watertight'] for r in data),'all_vertex_manifold':all(r['vertex_manifold'] for r in data),'total_quads':sum(r['quads'] for r in data),'sample':info,'models':data}
(R/'results/summary.json').write_text(json.dumps(summary,indent=2))
with (R/'results/validation.csv').open('w') as f:
 writer=csv.writer(f);writer.writerow(['id','name','quads','watertight','vertex_manifold','boundary_edges','self_intersection_pairs','components','exact_source_surface','rms_pct_diagonal','p95_pct_diagonal','max_sample_pct_diagonal'])
 for r in data:writer.writerow([r[k] for k in ['id','name','quads','watertight','vertex_manifold','boundary_edges','self_intersection_pairs','components','exact_source_surface']]+[r['quality'][k] for k in ['rms_percent_bbox_diagonal','p95_percent_bbox_diagonal','max_sample_percent_bbox_diagonal']])
print('GALLERY',len(data))
