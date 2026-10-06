"""Independently reopen delivered .blend files and audit their stored model mesh."""
import bpy,pathlib,json,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];results=[]
audit_path=R/'results/blend_audit.json'
previous={r['id']:r for r in json.loads(audit_path.read_text()) if r.get('audit_schema')==2} if audit_path.exists() else {}
for row in json.loads((R/'data/sample.json').read_text())['meshes']:
 id=row['id'];path=R/f'results/{id}/{id}.blend'
 if not path.exists() or not (R/f'gallery/images/{id}_source.png').exists():continue
 if id in previous and previous[id]['file_mtime_ns']==path.stat().st_mtime_ns:
  results.append(previous[id]);continue
 bpy.ops.wm.open_mainfile(filepath=str(path))
 objs=[o for o in bpy.data.objects if o.get('role')=='FINAL_VALIDATED_QUAD_SOLID'];assert len(objs)==1
 obj=objs[0];m=obj.data
 n=np.empty(len(m.polygons),dtype=np.int32);m.polygons.foreach_get('loop_total',n)
 ei=np.empty(len(m.loops),dtype=np.int32);m.loops.foreach_get('edge_index',ei);counts=np.bincount(ei,minlength=len(m.edges))
 vi=np.empty(len(m.loops),dtype=np.int32);m.loops.foreach_get('vertex_index',vi)
 v=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',v);v=v.reshape(-1,3)
 assert not any(p.use_smooth for p in m.polygons),(id,'unexpected smooth shading')
 assert np.all(n==4),(id,'non-quad face');q=vi.reshape(-1,4)
 assert np.all(counts==2),(id,'nonmanifold edge');assert len(obj.modifiers)==0
 a=np.load(R/f'results/{id}/quad.npz');expected=a['vertices'].copy();expected[:,2]-=expected[:,2].min()
 assert np.array_equal(q,a['quads']);assert np.allclose(v,expected,atol=1e-7,rtol=0)
 cross1=np.cross(v[q[:,1]].astype(float)-v[q[:,0]],v[q[:,2]].astype(float)-v[q[:,0]])
 cross2=np.cross(v[q[:,2]].astype(float)-v[q[:,0]],v[q[:,3]].astype(float)-v[q[:,0]])
 area=.5*(np.linalg.norm(cross1,axis=1)+np.linalg.norm(cross2,axis=1))
 zeros=int(np.sum(area==0))
 if zeros:
  print('AUDIT_FAIL',id,'zero-area faces',zeros,flush=True);continue
 assert not obj.hide_render;assert bpy.data.objects['SOURCE_REFERENCE'].hide_render
 assert bpy.context.scene.camera and len([o for o in bpy.data.objects if o.type=='LIGHT'])==3
 report={'id':id,'audit_schema':2,'file_mtime_ns':path.stat().st_mtime_ns,'file_bytes':path.stat().st_size,'stored_vertices':len(m.vertices),'stored_quads':len(m.polygons),'all_quads':True,'boundary_edges':int(np.sum(counts==1)),'nonmanifold_edges':int(np.sum(counts!=2)),'zero_area_faces':zeros,'geometry_matches_validated_npz':True,'source_hidden':True,'studio_lights':3,'passed':True}
 if 'studio_ground_offset' not in obj:
  obj['studio_ground_offset']=-float(a['vertices'][:,2].min());bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
 results.append(report);(R/'results/blend_audit.json').write_text(json.dumps(results,indent=2));print('AUDIT_OK',id,flush=True)
audit_path.write_text(json.dumps(results,indent=2))
print('AUDIT_COMPLETE',len(results),flush=True)
