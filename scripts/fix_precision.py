import sys,pathlib,json,numpy as np
from meshlib import mrmeshpy as m,mrmeshnumpy as n
R=pathlib.Path(__file__).resolve().parents[1];id=int(sys.argv[1]);out=R/f'results/{id}';a=np.load(out/'quad.npz');v=a['vertices'];f=a['quads'].reshape(-1,3,4)[:,:,0];used,inv=np.unique(f,return_inverse=True);v=v[used];f=inv.reshape(-1,3)
mesh=n.meshFromFacesVerts(f.astype(np.int32),v.astype(np.float32));params=m.FixMeshDegeneraciesParams();params.maxDeviation=2e-6;params.tinyEdgeLength=2e-6;params.criticalTriAspectRatio=1e4;m.fixMeshDegeneracies(mesh,params);mesh.pack()
collisions=len(m.findSelfCollidingTriangles(m.MeshPart(mesh)));print('COLLISIONS',collisions,flush=True);assert collisions==0
np.savez_compressed(out/'repaired_override.npz',vertices=n.getNumpyVerts(mesh),faces=n.getNumpyFaces(mesh.topology));report=json.loads((out/'report.json').read_text());(out/'override_info.json').write_text(json.dumps({'voxel_size':report['voxel_size_percent_longest_axis']/100 if report['voxel_size_percent_longest_axis'] is not None else None,'precision_repair_tolerance_normalized':2e-6},indent=2));print('PRECISION_OVERRIDE_READY',id,flush=True)
