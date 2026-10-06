import pathlib,json,zipfile,hashlib,subprocess,sys
from PIL import Image,ImageDraw,ImageFont
R=pathlib.Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(R/'scripts/build_gallery.py')],check=True)
s=json.loads((R/'data/sample.json').read_text());summary=json.loads((R/'results/summary.json').read_text());audit=json.loads((R/'results/blend_audit.json').read_text())
assert summary['completed']==100 and len(audit)==100 and all(a['passed'] for a in audit)
assert {a['id'] for a in audit}=={r['id'] for r in s['meshes']}
for row in s['meshes']:
 id=row['id'];assert (R/f'results/{id}/{id}.blend').stat().st_size>1000
 for suffix in ['', '_source']:assert (R/f'gallery/images/{id}{suffix}.png').exists()
width=2600;cw=260;ch=282;top=145
im=Image.new('RGB',(width,top+10*ch+55),'#f3f1e9');draw=ImageDraw.Draw(im)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';large=ImageFont.truetype(font,48);small=ImageFont.truetype(font,14);med=ImageFont.truetype(font,20)
draw.text((28,25),'100 FORMS / THINGI10K QUAD GALLERY',font=large,fill='#26362f');draw.text((30,90),'100 random meshes  ·  All-quad, watertight models  ·  Studio renders  ·  Source attribution in the gallery',font=med,fill='#667467')
for i,row in enumerate(s['meshes']):
 id=row['id'];img=Image.open(R/f'gallery/images/{id}.png').convert('RGB');img.thumbnail((250,250));x=(i%10)*cw+5;y=top+(i//10)*ch
 im.paste(img,(x,y));draw.text((x+4,y+253),f"{i+1:03d} / {id}",font=small,fill='#26362f')
im.save(R/'gallery/contact-sheet.jpg',quality=93);im.resize((1300,im.height//2)).save(R/'gallery/contact-sheet-small.jpg',quality=90)
# A portable review bundle: all Blender scenes, photographs, reports and attribution.
paths=[R/'README.txt',R/'requirements.txt',R/'data/sample.json',R/'gallery/index.html',R/'gallery/contact-sheet.jpg',R/'gallery/contact-sheet-small.jpg']
paths+=list((R/'gallery/images').glob('*.png'))+list((R/'results').glob('*.json'))+list((R/'results').glob('*.csv'))
paths+=list((R/'results').glob('*/*.blend'))+list((R/'results').glob('*/*.json'))
paths+=list((R/'scripts').glob('*.py'))+list((R/'data/metadata').glob('*.csv'))
with zipfile.ZipFile(R/'thingi10k-100-blends.zip','w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
 for p in paths:z.write(p,p.relative_to(R))
 print('BUNDLE_FILES',len(paths),flush=True)
# Avoid holding the large archive in memory for hashing.
h=hashlib.sha256()
with (R/'thingi10k-100-blends.zip').open('rb') as f:
 for chunk in iter(lambda:f.read(16*1024*1024),b''):h.update(chunk)
(R/'thingi10k-100-blends.zip.sha256').write_text(h.hexdigest()+'  thingi10k-100-blends.zip\n')
print('FINALIZED',summary['completed'],(R/'thingi10k-100-blends.zip').stat().st_size,flush=True)
