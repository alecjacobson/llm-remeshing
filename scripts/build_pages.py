"""Build the static Pages site without copying any LFS objects into the site."""
import csv,html,json,pathlib,shutil
R=pathlib.Path(__file__).resolve().parents[1];D=R/'docs';D.mkdir(exist_ok=True)
repo='alecjacobson/llm-remeshing'
base=f'https://media.githubusercontent.com/media/{repo}/main'
page=(R/'gallery/index.html').read_text()
page=page.replace('href="../data/','href="data/').replace('href="../results/','href="results/')
page=page.replace('href="results/${d.id}/${d.id}.blend"',f'href="{base}/results/${{d.id}}/${{d.id}}.blend"')
page=page.replace('<a href="../thingi10k-100-blends.zip" download>Download all 100 Blender scenes ↓</a>', '<a href="downloads.html">Download models with Git LFS ↓</a>')
page=page.replace('<p>Source designs belong', '<p><a href="attribution.html">Full attribution and per-model licenses</a><br>Source designs belong')
(D/'index.html').write_text(page);(D/'.nojekyll').touch()
for src,target in [(R/'gallery/images',D/'images')]:shutil.copytree(src,target,dirs_exist_ok=True)
for name in ['contact-sheet.jpg','contact-sheet-small.jpg']:shutil.copy2(R/'gallery'/name,D/name)
(D/'data').mkdir(exist_ok=True);shutil.copy2(R/'data/sample.json',D/'data/sample.json')
(D/'results').mkdir(exist_ok=True)
for p in (R/'results').glob('*.json'):shutil.copy2(p,D/'results'/p.name)
shutil.copy2(R/'results/validation.csv',D/'results/validation.csv')
for p in (R/'results').glob('*/*.json'):
 dst=D/'results'/p.parent.name/p.name;dst.parent.mkdir(exist_ok=True);shutil.copy2(p,dst)
style='body{max-width:1000px;margin:50px auto;padding:0 24px;font:16px/1.65 system-ui;background:#f3f1e9;color:#26362f}a{color:#3d634d}pre{padding:20px;overflow:auto;background:#e7e9df}table{border-collapse:collapse;width:100%;font-size:13px}td,th{text-align:left;padding:10px;border-bottom:1px solid #d3d8cd}h1{font:46px Georgia}'
def document(title,content):return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><style>'+style+'</style></head><body><a href="index.html">← Gallery</a><h1>'+title+'</h1>'+content+'</body></html>'
s=json.loads((R/'data/sample.json').read_text());rows=[]
for r in s['meshes']:
 c=r['context'];id=r['id'];rows.append('<tr><td>'+str(id)+'</td><td><a href="https://www.thingiverse.com/thing:'+str(r['source']['Thing ID'])+'">'+html.escape(html.unescape(c['Name']).strip())+'</a></td><td>'+html.escape(c['Author'])+'</td><td>'+html.escape(c['License'])+'</td></tr>')
(D/'attribution.html').write_text(document('Attribution & licenses','<p>Each source design and its technical mesh conversion retain the source model’s license shown below. There is no blanket license for this collection. NonCommercial, ShareAlike, and NoDerivatives conditions continue to apply where specified. The dataset catalog does not identify license version numbers; follow the linked original design for its authoritative terms.</p><p>Changes are documented in each validation report: normalization, orientation correction, topology conversion, and geometric repairs where needed. Studio presentation adds materials, lighting, and cameras. These technical results do not grant permission to make or redistribute further adaptations contrary to the source license.</p><p>Dataset: Qingnan Zhou and Alec Jacobson, <a href="https://github.com/Thingi10K/Thingi10K">Thingi10K: A Dataset of 10,000 3D-Printing Models</a>, 2016. <a href="data/sample.json">Full source URLs, provenance, and hashes</a>.</p><table><thead><tr><th>File ID</th><th>Design / original source</th><th>Creator</th><th>License in dataset</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'))
commands=f'git lfs install\nGIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/{repo}.git\ncd llm-remeshing\ngit lfs pull --include="results/*/*.blend"'
(D/'downloads.html').write_text(document('Download the models','<p>All 100 Blender scenes and the source/result mesh arrays are stored with Git LFS. Use each gallery card for an individual Blender download, or fetch all scenes:</p><pre>'+html.escape(commands)+'</pre><p>To also download the original mesh arrays, quad arrays, and repair intermediates:</p><pre>git lfs pull</pre><p>GitHub’s ordinary source ZIP may contain LFS pointers instead of the binary assets; cloning with Git LFS retrieves the actual files. The full Blender collection is approximately 2.6 GB. All models retain their <a href="attribution.html">individual source licenses</a>.</p><p><a href="https://github.com/'+repo+'">Browse repository</a> · <a href="results/validation.csv">Download validation CSV</a></p>'))
assert len(list((D/'images').glob('*.png')))==200
assert not list(D.rglob('*.blend')) and not list(D.rglob('*.npz'))
print('PAGES_BUILD_OK',sum(p.stat().st_size for p in D.rglob('*') if p.is_file()))
