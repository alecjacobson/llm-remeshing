"""Blender 4.5: studio scene, source comparison, all-quad .blend deliverable."""
import bpy,sys,json,pathlib,math,time
import numpy as np
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[1]
id=int(sys.argv[sys.argv.index('--')+1]);out=ROOT/'results'/str(id)
row=next(r for r in json.loads((ROOT/'data/sample.json').read_text())['meshes'] if r['id']==id)
report=json.loads((out/'report.json').read_text());a=np.load(out/'quad.npz')
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=32;scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='CUDA';prefs.get_devices()
for dev in prefs.devices:dev.use=dev.type=='CUDA'
scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world=bpy.data.worlds.new('Studio ambient');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.19,.23,.3,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.25
scene.view_settings.view_transform='AgX'

def mesh_object(name,v,f,collection=None):
 mesh=bpy.data.meshes.new(name);mesh.vertices.add(len(v));mesh.vertices.foreach_set('co',np.asarray(v,dtype=np.float32).ravel());mesh.loops.add(f.size);mesh.loops.foreach_set('vertex_index',np.asarray(f,dtype=np.int32).ravel());mesh.polygons.add(len(f));mesh.polygons.foreach_set('loop_start',np.arange(len(f),dtype=np.int32)*f.shape[1]);mesh.polygons.foreach_set('loop_total',np.full(len(f),f.shape[1],dtype=np.int32));mesh.polygons.foreach_set('use_smooth',np.zeros(len(f),dtype=bool));mesh.update()
 obj=bpy.data.objects.new(name,mesh);(collection or scene.collection).objects.link(obj);return obj

palette=[(.08,.29,.32,1),(.30,.43,.54,1),(.54,.26,.12,1),(.35,.32,.44,1),(.32,.40,.26,1),(.56,.45,.29,1)]
mat=bpy.data.materials.new('Satin ceramic · gallery edition');mat.diffuse_color=palette[(row['index']-1)%len(palette)];mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=mat.diffuse_color;bsdf.inputs['Metallic'].default_value=.18;bsdf.inputs['Roughness'].default_value=.30
v=a['vertices'].copy();v[:,2]-=v[:,2].min();q=a['quads']
obj=mesh_object(f"Thingi10K_{id}_QUAD",v,q);obj.data.materials.append(mat)
# Flat normals preserve original CAD facets and avoid shading distortions on skinny quads.
obj['role']='FINAL_VALIDATED_QUAD_SOLID';obj['thingi10k_file_id']=id;obj['author']=row['context']['Author'];obj['license']=row['context']['License'];obj['method']=report['method'];obj['source_scale']=float(a['source_scale']);obj['source_center']=a['source_center'].tolist();obj['studio_ground_offset']=-float(a['vertices'][:,2].min());obj['validation_report']=json.dumps(report)
# Keep source geometry in the same scene, disabled by default for clean delivery.
ref=bpy.data.collections.new('REFERENCE · original triangles (hidden)');scene.collection.children.link(ref)
s=np.load(ROOT/'data/source'/f'{id}.npz');sv=(s['vertices']-a['source_center'])/a['source_scale'];sv[:,2]-=a['vertices'][:,2].min()
source=mesh_object('SOURCE_REFERENCE',sv,s['facets'],ref);source.data.materials.append(mat);source.hide_render=True;source.hide_set(True)
source['role']='SOURCE_REFERENCE_ONLY'
# This source was exported upside down; present the articulated puppy upright.
# Geometry remains in its audited local coordinate system; this is a rigid object transform.
if id==1258096:
 for display in [obj,source]:
  display.rotation_euler.x=math.pi;display.location.z=float(v[:,2].max())
 obj['presentation_note']='Rigid 180-degree X rotation for upright studio presentation; vertex data unchanged.'
# A closed quad cube provides the seamless studio floor.
bpy.ops.mesh.primitive_cube_add(size=2,location=(0,0,-.036));ground=bpy.context.object;ground.name='STUDIO · floor';ground.scale=(200,200,.035)
fmat=bpy.data.materials.new('Warm chalk');fmat.diffuse_color=(.72,.70,.65,1);fmat.use_nodes=True;fmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=fmat.diffuse_color;fmat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.82;ground.data.materials.append(fmat)
center=Vector((0,0,float(v[:,2].max())*.48))
def aim(o,target):o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
def camera(name,direction):
 data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=center+Vector(direction).normalized()*3;aim(o,center);data.type='ORTHO'
 rot=o.rotation_euler.to_matrix().transposed();corners=[Vector((x,y,z)) for x in [v[:,0].min(),v[:,0].max()] for y in [v[:,1].min(),v[:,1].max()] for z in [0,v[:,2].max()]]
 coords=[rot@(c-center) for c in corners];data.ortho_scale=max(max(c.x for c in coords)-min(c.x for c in coords),max(c.y for c in coords)-min(c.y for c in coords))*1.25
 return o
cam=camera('CAMERA · front three-quarter',(1.4,-2.1,1.35));scene.camera=cam
camera('CAMERA · reverse',(-1.6,2.1,1.25));camera('CAMERA · top',(.01,-.01,3))
def area(name,loc,power,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;aim(o,center)
area('SOFTBOX · key',(-1.8,-2.2,3.1),210,2.4,(1,.88,.72));area('SOFTBOX · fill',(2,-.4,1.8),100,2,(.72,.84,1));area('SOFTBOX · rim',(.4,2,2.6),260,1.8,(1,.95,.86))
text=bpy.data.texts.new('READ ME · model and validation');text.write(json.dumps({'source':row,'validation':report,'notes':['Final model object is tagged FINAL_VALIDATED_QUAD_SOLID.','All final polygons have four vertices; geometry is baked, no remesh modifier required.','Original source is retained in the hidden REFERENCE collection.','Model is normalized to longest source bounding-box axis = 1; original scale and center are stored as custom properties.','Quad layout prioritizes surface fidelity, not animation edge flow.','Multiple disconnected solid components are retained where present.']},indent=2))
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
for screen in bpy.data.screens:
 for ar in screen.areas:
  if ar.type=='VIEW_3D':ar.spaces.active.region_3d.view_perspective='CAMERA'
scene.render.filepath=str(ROOT/'gallery/images'/f'{id}.png')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{id}.blend'),compress=True)
bpy.ops.render.render(write_still=True)
obj.hide_render=True;source.hide_render=False;source.hide_set(False);scene.render.filepath=str(ROOT/'gallery/images'/f'{id}_source.png');bpy.ops.render.render(write_still=True)
# Saved scene was written with the final model visible and the reference hidden.
print('RENDER_DONE',id,flush=True)
