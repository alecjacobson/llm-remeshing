import numpy as np,pathlib
from meshlib import mrmeshpy as m,mrmeshnumpy as n
R=pathlib.Path(__file__).resolve().parents[1];p=R/'results/252786/repaired_override.npz';a=np.load(p);mesh=n.meshFromFacesVerts(a['faces'].astype(np.int32),a['vertices'].astype(np.float32));settings=m.DecimateSettings();settings.maxError=1/768*.12;settings.maxTriangleAspectRatio=20;settings.packMesh=True
print('DECIMATE',mesh.topology.numValidFaces(),flush=True);m.decimateMesh(mesh,settings);print('DECIMATED',mesh.topology.numValidFaces(),flush=True)
for i in range(8):
 pairs=m.findSelfCollidingTriangles(m.MeshPart(mesh));print('COLLISIONS',i,len(pairs),flush=True)
 if not len(pairs):
  mesh.pack();np.savez_compressed(p,vertices=n.getNumpyVerts(mesh),faces=n.getNumpyFaces(mesh.topology));print('COMPACT_READY',flush=True);break
 fix=m.SelfIntersections.Settings();fix.method=m.SelfIntersections.Settings.Method.Relax if i%2==0 else m.SelfIntersections.Settings.Method.CutAndFill;fix.maxExpand=3+i*2;fix.relaxIterations=5+i*2;fix.touchIsIntersection=True;m.SelfIntersections.fix(mesh,fix)
else:raise RuntimeError('Keeping previous valid override')
