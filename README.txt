PUBLIC GALLERY: https://alecjacobson.github.io/llm-remeshing/
REPOSITORY: https://github.com/alecjacobson/llm-remeshing

Git LFS stores all .blend and .npz files. Run git lfs install before cloning,
or git lfs pull after cloning, to download the actual binary files.
The optional 2.76 GB local ZIP is excluded from Git; the public site provides
individual downloads and instructions to retrieve all scenes with Git LFS.
The static Pages site is built with python scripts/build_pages.py into docs/.

100 FORMS — THINGI10K QUAD GALLERY

Open gallery/index.html in a browser. It works offline without a web server.
Each card opens an original/result comparison, geometric measurements, source
attribution, the validation report, and a .blend download.

DELIVERABLES
  results/<file_id>/<file_id>.blend  Editable Blender 4.5 studio scenes
  results/<file_id>/quad.npz         Validated vertices and quad face indices
  results/<file_id>/report.json      Geometry and surface-distance measurements
  results/summary.json               Consolidated model reports
  results/validation.csv             Spreadsheet-friendly validation table
  results/blend_audit.json           Independent checks of saved Blender meshes
  gallery/images/                    Matched source/result studio photographs
  gallery/contact-sheet.jpg         Overview of all 100 results
  thingi10k-100-blends.zip           Portable gallery, Blender files, reports, scripts
                                    (source/quad NPZ files stay in the workspace)
  data/sample.json                  Seed, IDs, attribution, URLs, source SHA-256
  data/source/                      Only the 100 sampled geometry files

SAMPLING
The sample is uniform without replacement over all 10,000 file IDs, sorted
numerically, using Python random.Random(seed).sample(ids, 100).
Seed: 1623326664713734764
Pinned dataset revision: 2d5d3b2f3cd3711028ad75b12788c13b25559ec6
No filtering or substitution by category, mesh size, license, or repair difficulty.
The 100 geometry downloads total 197,107,528 bytes. Only catalog metadata was
fetched in addition; no dataset archive or full-dataset initialization was used.

GEOMETRY
Intact solids retain their original piecewise-linear surfaces. Defective inputs
are cleaned, oriented, and, when needed, reconstructed using MeshLib's generalized
winding-number signed-distance field. Default voxel spacing is 1/640 of the
longest bounding-box axis; reports disclose reconstruction resolution.
Nested shells use alternating orientation to preserve cavities. Multiple shells
are retained, and intersecting volumes are resolved during solid reconstruction.

Each triangle becomes three planar quadrilaterals using a shared midpoint on
every edge and a center in each face. This produces a pure-quad closed mesh while
preserving the repaired surface. It is a dense geometric representation, not
artist-directed retopology for animation or a low-poly subdivision control cage.
The saved geometry requires no modifiers to satisfy the quad requirement.

Validation checks edge incidence, winding, vertex manifoldness, positive volume,
and self-intersections on the triangle surface before exact quad subdivision.
Blender files are independently reopened to check actual saved polygons, edge
incidence, zero-area faces, and agreement with validated vertex/face arrays.
Distance reports use 12,000 deterministic area-uniform samples in each direction
plus up to 12,000 original vertices. They are NOT certified Hausdorff bounds.
Reconstruction can change very thin features, repair holes, and remove overlapping
interior surfaces. Inspect comparison photos and each report for local details.

BLENDER SCENES
Select the object tagged role = FINAL_VALIDATED_QUAD_SOLID. The original triangle
mesh is retained in a hidden REFERENCE collection. The floor is a separate closed
cube. Three area lights, a satin ceramic material, and front/reverse/top cameras
are included. The final model is visible and the reference is hidden on opening.

Mesh-local studio coordinates normalize the source's longest axis to 1 and ground the model.
The object stores source_scale, source_center, and studio_ground_offset.
Restore source coordinates from mesh-local vertices with:
  source_vertex = (studio_vertex - (0,0,studio_ground_offset)) * source_scale
                  + source_center
A rigid object transform presents the puppy (1258096) upright; its mesh-local
vertices and stored source transform remain unchanged.
Source files do not establish a universal physical unit; no unit is assumed.

REPRODUCE
Python packages are pinned in requirements.txt. Blender 4.5.3 LTS was used.
The current reconstruction and rendering scripts use an NVIDIA CUDA device.
  python scripts/download_sample.py
  python scripts/sample_catalog.py --verify
  python scripts/run_processing.py
  BLENDER_BIN=/path/to/blender python scripts/run_rendering.py
  /path/to/blender -b --python scripts/audit_blends.py
  python scripts/build_gallery.py
  python scripts/test_gallery.py
Scripts resume from existing completed outputs. To intentionally rebuild a model,
run process_mesh.py <id>, then Blender --python make_blend.py -- <id>.
The catalog verifier also checks all downloaded source hashes and rejects extra IDs.

SOURCES AND ATTRIBUTION
Dataset: https://github.com/Thingi10K/Thingi10K
Individual files: https://huggingface.co/datasets/Thingi10K/Thingi10K
Qingnan Zhou and Alec Jacobson, Thingi10K: A Dataset of 10,000 3D-Printing Models,
arXiv:1605.04797 (2016).

Individual designs retain their own licenses, listed in the manifest, gallery,
and embedded Blender text. Some source licenses restrict derivative redistribution;
the public collection retains each source model’s terms; see LICENSES.txt.

Repair documentation:
https://meshlib.io/documentation/ExampleCudaOffset.html
https://meshlib.io/blog/mesh-repair-for-boolean-operations/
