<img src="assets/icon.svg" width="64" height="64" alt="">

# PicoGK learning lab

Our first model is a 30 × 30 × 16 mm open-top desk tray. Build a solid
box, subtract a smaller raised box, then export the remaining material.
All dimensions are in millimetres.

We use [PicoPie](https://github.com/inventhq/PicoPie), a community Python
binding for LEAP 71's PicoGK geometry kernel. This is the Python route;
the official PicoGK API uses C#.

## Setup and run

Use Python 3.12 (the system Python 3.14 is outside this release's documented
wheel support). With uv installed:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python main.py
```

Open `output/desk_tray.stl` in your preferred mesh viewer or slicer.
Or open the built-in interactive viewer directly:

```bash
.venv/bin/python main.py --view
# With lattice fill:
.venv/bin/python main.py --gyroid --view
```

Drag with the left mouse button to rotate, scroll to zoom, and Shift-drag
to pan. Press F to fit the model, or Esc to close. Close and rerun after
editing parameters; the viewer does not reload edits automatically.

### Gyroid cross sections

```bash
# Vertical cut through the middle (X = 0):
.venv/bin/python main.py --gyroid --section x
# Horizontal cut halfway up:
.venv/bin/python main.py --gyroid --section z
# Horizontal cut at Z = 3 mm above the bottom:
.venv/bin/python main.py --gyroid --section z --cut-at 3
```

The section option opens the viewer automatically. It removes the positive
side of the selected plane from the display, exposing the cut faces.
Rotate to look straight at the cut face or inspect it at an angle.
The main STL contains the complete tray. A separate file such as
`output/gyroid_tray_section_x.stl` contains the cutaway and is saved before
the viewer opens. It can also be opened in another mesh viewer.
X and Y are centred on the tray; Z starts at the bottom.

`--gyroid` adds the lattice in code before export (no slicer infill setting
needed). Adjust `GYROID_CELL_MM` for cell spacing and
`GYROID_WALL_MM` for approximate lattice wall thickness. `SKIN_MM` sets
the solid skin around all surfaces, including the cavity and rim.

The current STL examples are saved in Git. The virtual environment and
temporary viewer settings are ignored.
These are geometry exercises, not validated manufacturing files.

## First experiment

1. Run the default model. Read the volume and bounding dimensions printed.
2. In `main.py`, change `HEIGHT_MM` from `16.0` to `20.0`.
3. Run again and reopen the STL. The floor thickness stays the same while
   the sidewalls get taller. The printed volume should increase.
4. Restore the height to 16 mm, then try `.venv/bin/python main.py --gyroid`.
   This writes `output/gyroid_tray.stl`, with gyroid enclosed inside the walls and floor; the cavity stays empty.

## What the code means

- `Box(...).to_voxels()` turns a parametric box into a sampled volume.
- `LocalFrame(position=...)` positions the cutter above the floor.
- `outer - cavity` removes material. `+` joins volumes; `&` intersects them.
- The cutter extends through the top so the tray opens there.
- `to_mesh().save_stl(...)` converts the volume into triangles for export.

`VOXEL_MM = 0.2` controls sampling resolution. The demonstration uses
6 mm walls and floor, with 0.8 mm skins and approximately 0.8 mm lattice walls. Smaller voxels resolve finer features but cost memory
and time. Dimensions and volumes are approximate because of sampling.
The script measures volume from oriented mesh triangles so enclosed voids
are counted correctly, and compares the plain tray with its analytic
box-minus-box volume. PicoPie 0.7.0 `calculate_properties()` reimports the
mesh and fills enclosed voids in this setup; avoid it for enclosed infill.

The optional gyroid uses a 6 mm unit cell. PicoPie converts our approximate
physical wall thickness to its dimensionless implicit thickness ratio.
The core lies inside an inward offset of the tray material, outside the open cavity.
Solid skins enclose the core; a section through the walls/floor exposes it.

References: [PicoGK](https://picogk.org),
[PicoPie documentation](https://github.com/inventhq/PicoPie#documentation).

Viewer limitation observed here: native screenshot capture aborted inside
PicoGK viewer redraw. Avoid the S screenshot key for now; ordinary interactive
viewing is tested separately. Geometry exports are saved before opening it.
