import pathlib,sys,numpy as np,time
from meshlib import mrmeshpy as m,mrmeshnumpy as n
R=pathlib.Path(__file__).resolve().parents[1];id=int(sys.argv[1]);out=R/f'results/{id}';a=np.load(out/'repair_checkpoint.npz');mesh=n.meshFromFacesVerts(a['faces'].astype(np.int32),a['vertices'].astype(np.float32))
for i in range(8):
 pairs=m.findSelfCollidingTriangles(m.MeshPart(mesh));print('INTERSECTIONS',i,len(pairs),flush=True)
 if not len(pairs):
  mesh.pack();np.savez_compressed(out/'repaired_override.npz',vertices=n.getNumpyVerts(mesh),faces=n.getNumpyFaces(mesh.topology));print('OVERRIDE_READY',flush=True);break
 settings=m.SelfIntersections.Settings();settings.method=m.SelfIntersections.Settings.Method.Relax if i%2==0 else m.SelfIntersections.Settings.Method.CutAndFill;settings.maxExpand=3+i*2;settings.relaxIterations=5+i*2;settings.touchIsIntersection=True
 m.SelfIntersections.fix(mesh,settings)
else:raise RuntimeError('Local repair failed')
