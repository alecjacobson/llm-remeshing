"""Repair sampled geometry, preserve surfaces with exact all-quad subdivision, validate."""
import os,sys,time,json,pathlib
os.environ['OMP_NUM_THREADS']='4'; os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np, trimesh, igl
from meshlib import mrmeshpy as mm,mrmeshnumpy as mn,mrcudapy as mc
ROOT=pathlib.Path(__file__).resolve().parents[1]

def solid_angle_winding(vertices,faces,point):
 tri=vertices[faces]-point
 a,b,c=tri[:,0],tri[:,1],tri[:,2];la,lb,lc=np.linalg.norm(a,axis=1),np.linalg.norm(b,axis=1),np.linalg.norm(c,axis=1)
 numerator=np.einsum('ij,ij->i',a,np.cross(b,c))
 denominator=la*lb*lc+np.einsum('ij,ij->i',a,b)*lc+np.einsum('ij,ij->i',b,c)*la+np.einsum('ij,ij->i',c,a)*lb
 return float(np.arctan2(numerator,denominator).sum()/(2*np.pi))

def arrays(mesh):
 mesh.pack(); return mn.getNumpyVerts(mesh).copy().astype(np.float64),mn.getNumpyFaces(mesh.topology).copy().astype(np.int64)

def topology(v,f):
 t=trimesh.Trimesh(v,f,process=False)
 vm=bool(np.all(igl.is_vertex_manifold(f)))
 return {'watertight':bool(t.is_watertight),'winding_consistent':bool(t.is_winding_consistent),'vertex_manifold':vm,'volume':float(t.volume),'components':int(len(trimesh.graph.connected_components(t.face_adjacency,nodes=np.arange(len(f)),min_len=1)))}

def run(id):
 start=time.time(); row=next(r for r in json.loads((ROOT/'data/sample.json').read_text())['meshes'] if r['id']==id)
 out=ROOT/'results'/str(id);out.mkdir(exist_ok=True)
 data=np.load(ROOT/'data/source'/f'{id}.npz'); ov=data['vertices'].astype(float); of=data['facets'].astype(np.int64)
 center=(ov.max(0)+ov.min(0))/2;scale=float(np.ptp(ov,axis=0).max());ov=(ov-center)/scale
 source=trimesh.Trimesh(ov,of,process=True);source.update_faces(source.nondegenerate_faces());source.update_faces(source.unique_faces());source.remove_unreferenced_vertices()
 certified_clean=bool(row['geometry']['solid'] and not row['geometry']['num_self_intersections'] and source.is_watertight and source.is_winding_consistent and source.volume>0)
 if not certified_clean and not (out/'repaired_override.npz').exists():
  trimesh.repair.fix_normals(source,multibody=True)
  # Orient each disconnected face component independently, including open components.
  # trimesh.fix_normals does not invert components when the combined input is open.
  groups=trimesh.graph.connected_components(source.face_adjacency,nodes=np.arange(len(source.faces)),min_len=1)
  sf=source.faces.copy()
  for group in groups:
   if len(group)<4: continue
   tris=source.vertices[sf[group]];local_center=tris.reshape(-1,3).mean(0);tris=tris-local_center
   volume=np.einsum('ij,ij->i',tris[:,0],np.cross(tris[:,1],tris[:,2])).sum()/6
   if volume < -1e-12:sf[group]=sf[group][:,::-1]
  # Nested closed shells bound cavities: alternate orientation by containment depth.
  if not row['geometry']['num_self_intersections'] and source.is_watertight and len(groups)>1:
   bounds=[(source.vertices[sf[group]].min(axis=(0,1)),source.vertices[sf[group]].max(axis=(0,1))) for group in groups]
   compact=[]
   for group in groups:
    used,local=np.unique(sf[group],return_inverse=True);compact.append((np.asarray(source.vertices)[used],local.reshape(-1,3)))
   for gi,group in enumerate(groups):
    point=source.vertices[sf[group[0]]].mean(0);depth=0;group_lo,group_hi=bounds[gi]
    for gj,other in enumerate(groups):
     if gi==gj or len(other)<4:continue
     lo,hi=bounds[gj]
     if np.all(group_lo>=lo-1e-12) and np.all(group_hi<=hi+1e-12) and np.all(point>lo) and np.all(point<hi):
      winding=solid_angle_winding(compact[gj][0],compact[gj][1],point)
      if abs(winding)>.5:depth+=1
    if depth%2:sf[group]=sf[group][:,::-1]
  source.faces=sf
 v=np.asarray(source.vertices);f=np.asarray(source.faces)
 g=row['geometry']; initial=topology(v,f)
 exact=bool(not g['num_self_intersections'] and initial['watertight'] and initial['vertex_manifold'])
 mesh=mn.meshFromFacesVerts(f.astype(np.int32),v.astype(np.float32))
 method='Exact surface / triangle-to-three-quads'; voxel=None
 if exact:
  collisions=len(mm.findSelfCollidingTriangles(mm.MeshPart(mesh)))
  exact=collisions==0
 override=out/'repaired_override.npz'
 if override.exists():
  repaired=np.load(override);v=repaired['vertices'].astype(float);f=repaired['faces'].astype(np.int64);mesh=mn.meshFromFacesVerts(f.astype(np.int32),v.astype(np.float32));exact=False;voxel=json.loads((out/'override_info.json').read_text())['voxel_size'] if (out/'override_info.json').exists() else 1/768;method='Winding-number solid reconstruction with local intersection repair / exact quad subdivision';collisions=len(mm.findSelfCollidingTriangles(mm.MeshPart(mesh)))
 if not exact and not override.exists():
  voxel=1/640
  params=mm.GeneralOffsetParameters();params.voxelSize=voxel;params.signDetectionMode=mm.SignDetectionMode.HoleWindingRule;params.closeHolesInHoleWindingNumber=True
  # Standard marching-cubes reconstruction is stable; error-controlled decimation keeps detail.
  params.mode=mm.GeneralOffsetParameters.Mode.Standard
  params.fwn=mc.FastWindingNumber(mesh)
  print('RECONSTRUCT',id,flush=True)
  mesh=mm.generalOffsetMesh(mm.MeshPart(mesh),0.,params)
  print('DECIMATE',id,mesh.topology.numValidFaces(),flush=True)
  dec=mm.DecimateSettings();dec.maxError=voxel*.12;dec.maxTriangleAspectRatio=20;dec.packMesh=True
  mm.decimateMesh(mesh,dec)
  v,f=arrays(mesh);method='Winding-number solid reconstruction / exact quad subdivision'
  check=topology(v,f);collisions=len(mm.findSelfCollidingTriangles(mm.MeshPart(mesh)))
  if collisions:
   print('LOCAL_REPAIR',id,collisions,flush=True)
   settings=mm.SelfIntersections.Settings();settings.method=mm.SelfIntersections.Settings.Method.CutAndFill;settings.maxExpand=3;settings.relaxIterations=2
   mm.SelfIntersections.fix(mesh,settings);v,f=arrays(mesh)
   collisions=len(mm.findSelfCollidingTriangles(mm.MeshPart(mesh)));check=topology(v,f)
  if not check['watertight'] or not check['vertex_manifold'] or collisions:
   # Retry reconstruction without decimation in the rare event simplification creates contacts.
   params.voxelSize=1/768;voxel=params.voxelSize
   params.fwn=mc.FastWindingNumber(mesh)
   mesh=mm.generalOffsetMesh(mm.MeshPart(mesh),0.,params);v,f=arrays(mesh)
   collisions=len(mm.findSelfCollidingTriangles(mm.MeshPart(mesh)))
   if collisions:
    settings=mm.SelfIntersections.Settings();settings.method=mm.SelfIntersections.Settings.Method.CutAndFill;settings.maxExpand=5;settings.relaxIterations=3
    mm.SelfIntersections.fix(mesh,settings);v,f=arrays(mesh);collisions=len(mm.findSelfCollidingTriangles(mm.MeshPart(mesh)))
 else:
  # Keep original doubles when the source is already a solid.
  pass
 check=topology(v,f)
 if collisions:np.savez(out/'repair_checkpoint.npz',vertices=v,faces=f)
 assert check['watertight'] and check['winding_consistent'] and check['vertex_manifold'] and check['volume']>0 and collisions==0,(id,check,collisions)
 # One shared midpoint per edge, one center per triangle: exactly 3 planar quads/triangle.
 edges=np.stack([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]],axis=1)
 unique,inverse,counts=np.unique(np.sort(edges,axis=2).reshape(-1,2),axis=0,return_inverse=True,return_counts=True)
 assert np.all(counts==2)
 mids=inverse.reshape(-1,3)+len(v);centers=np.arange(len(f))+len(v)+len(unique)
 qv=np.concatenate([v,v[unique].mean(1),v[f].mean(1)])
 q=np.stack([np.stack([f[:,i],mids[:,i],centers,mids[:,(i-1)%3]],axis=1) for i in range(3)],axis=1).reshape(-1,4)
 # Independent edge incidence and direction checks on the actual quad mesh.
 qe=np.stack([q,np.roll(q,-1,axis=1)],axis=2).reshape(-1,2)
 ue,inv,cnt=np.unique(np.sort(qe,axis=1),axis=0,return_inverse=True,return_counts=True)
 direction=np.bincount(inv,weights=np.where(qe[:,0]<qe[:,1],1,-1))
 assert np.all(cnt==2) and np.all(direction==0)
 # Deterministic bidirectional area-uniform surface distance samples + original vertices.
 np.random.seed(id)
 final=trimesh.Trimesh(v,f,process=False)
 ps=source.sample(12000);pt=final.sample(12000)
 ds=np.sqrt(np.maximum(igl.point_mesh_squared_distance(ps,v,f)[0],0))
 dt=np.sqrt(np.maximum(igl.point_mesh_squared_distance(pt,ov,of)[0],0))
 dv=np.sqrt(np.maximum(igl.point_mesh_squared_distance(ov[np.linspace(0,len(ov)-1,min(12000,len(ov))).astype(int)],v,f)[0],0))
 diag=float(np.linalg.norm(np.ptp(ov,axis=0)))
 dist=np.concatenate([ds,dt]);quality={'sample_count_each_direction':12000,'rms_percent_bbox_diagonal':float(np.sqrt(np.mean(dist**2))/diag*100),'p95_percent_bbox_diagonal':float(np.percentile(dist,95)/diag*100),'max_sample_percent_bbox_diagonal':float(dist.max()/diag*100),'source_vertex_max_percent_bbox_diagonal':float(dv.max()/diag*100),'note':'Sampled distances, not a certified Hausdorff bound. Interior source surfaces count toward repair deviation.'}
 np.savez_compressed(out/'quad.npz',vertices=qv,quads=q,source_center=center,source_scale=scale)
 report={'id':id,'index':row['index'],'method':method,'exact_source_surface':exact,'voxel_size_percent_longest_axis':None if voxel is None else voxel*100,'source_vertices':len(ov),'source_triangles':len(of),'vertices':len(qv),'quads':len(q),'triangles':0,'ngons':0,'boundary_edges':int(np.sum(cnt==1)),'nonmanifold_edges':int(np.sum(cnt!=2)),'self_intersection_pairs':collisions,**check,'quality':quality,'source_transform':{'center':center.tolist(),'scale':scale},'processing_seconds':time.time()-start}
 (out/'report.json').write_text(json.dumps(report,indent=2));print('DONE',id,len(q),quality,flush=True)
if __name__=='__main__':run(int(sys.argv[1]))
