"""First PicoGK exercise: subtract a box from a box to make a desk tray."""

from pathlib import Path
import argparse
import numpy as np

import picopie
from picopie.shapes import Box, LocalFrame, ImplicitGyroid

# All dimensions are millimetres. Start by changing HEIGHT_MM to 20.
WIDTH_MM = 30.0
DEPTH_MM = 30.0
HEIGHT_MM = 16.0
WALL_MM = 6.0  # thick demonstration walls leave room for enclosed infill
FLOOR_MM = 6.0
VOXEL_MM = 0.2
GYROID_CELL_MM = 6.0
GYROID_WALL_MM = 0.8  # approximate physical thickness
SKIN_MM = 0.8  # solid material at every surface, including cavity and rim


def build_tray(gyroid=False):
    if not (0 < WALL_MM < min(WIDTH_MM, DEPTH_MM) / 2
            and 0 < FLOOR_MM < HEIGHT_MM):
        raise ValueError('Wall and floor thickness must leave an open cavity')
    # Box's length runs along Z; width and depth run along X and Y.
    outer = Box(length=HEIGHT_MM, width=WIDTH_MM, depth=DEPTH_MM).to_voxels()
    # Raise the cutter to leave a floor and extend it through the open top.
    cavity = Box(
        length=HEIGHT_MM,
        width=WIDTH_MM - 2 * WALL_MM,
        depth=DEPTH_MM - 2 * WALL_MM,
        frame=LocalFrame(position=(0, 0, FLOOR_MM)),
    ).to_voxels()
    tray = outer - cavity
    if gyroid:
        if min(SKIN_MM, GYROID_WALL_MM) < 3 * VOXEL_MM:
            raise ValueError('Skin and gyroid walls need at least three voxels across')
        if min(WALL_MM, FLOOR_MM) <= 2 * SKIN_MM + 3 * VOXEL_MM:
            raise ValueError('Walls/floor need room for two skins and an infill core')
        # Erode the MATERIAL, not the cavity: this leaves a protected skin
        # around the outside, cavity, bottom and top rim.
        lattice = ImplicitGyroid(
            unit_size=GYROID_CELL_MM,
            thickness_ratio=ImplicitGyroid.thickness_ratio_for(
                GYROID_WALL_MM, GYROID_CELL_MM))
        interior = tray.offset(-SKIN_MM)
        skins = tray - interior
        core = lattice.render(interior.bounding_box()) & interior
        tray = skins + core

    return tray


def section_view(tray, axis, position=None):
    """Keep material below a plane; only the display geometry is clipped."""
    sizes = [WIDTH_MM, DEPTH_MM, HEIGHT_MM]
    lower = [-WIDTH_MM / 2, -DEPTH_MM / 2, 0.0]
    index = 'xyz'.index(axis)
    if position is None:
        position = lower[index] + sizes[index] / 2
    if not lower[index] < position < lower[index] + sizes[index]:
        raise ValueError(f'Cut must lie inside the tray along {axis.upper()}')
    # Expand the other faces beyond the part so they do not trim it.
    margin = 4 * VOXEL_MM
    clip_size = [s + 2 * margin for s in sizes]
    clip_lower = [v - margin for v in lower]
    clip_size[index] = position - clip_lower[index]
    origin = (clip_lower[0] + clip_size[0] / 2,
              clip_lower[1] + clip_size[1] / 2, clip_lower[2])
    clip = Box(length=clip_size[2], width=clip_size[0], depth=clip_size[1],
               frame=LocalFrame(position=origin)).to_voxels()
    return tray & clip


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gyroid', action='store_true', help='use enclosed gyroid infill inside walls and floor')
    parser.add_argument('--view', action='store_true', help='open the interactive 3D viewer')
    parser.add_argument('--section', choices=['x', 'y', 'z'],
                        help='open a cutaway viewer normal to this axis (default: midpoint)')
    parser.add_argument('--cut-at', type=float, metavar='MM',
                        help='section plane coordinate in mm; requires --section')
    args = parser.parse_args()
    if args.cut_at is not None and not args.section:
        parser.error('--cut-at requires --section')
    picopie.init(voxel_size_mm=VOXEL_MM)
    tray = build_tray(args.gyroid)
    mesh = tray.to_mesh()
    bounds = mesh.bounding_box()
    # calculate_properties() re-voxelizes the mesh and fills enclosed voids
    # in this release. Measure oriented mesh volume to retain those voids.
    triangles = mesh.vertices[mesh.triangles].astype(np.float64)
    volume = abs(np.einsum('ij,ij->i', triangles[:, 0],
                 np.cross(triangles[:, 1], triangles[:, 2])).sum()) / 6
    ideal = WIDTH_MM * DEPTH_MM * HEIGHT_MM - (
        (WIDTH_MM - 2 * WALL_MM) * (DEPTH_MM - 2 * WALL_MM)
        * (HEIGHT_MM - FLOOR_MM)
    )
    print(f'Volume: {volume:.1f} mm^3')
    print('Bounds: ' + ' x '.join(f'{v:.2f}' for v in bounds.size) + ' mm')
    print(f'Triangles: {len(mesh.triangles)}')
    if not args.gyroid:
        print(f'Ideal sharp-corner volume: {ideal:.1f} mm^3 (voxel approximation differs)')
        if abs(volume - ideal) / ideal > 0.15:
            raise RuntimeError('Unexpected tray volume; inspect geometry before export.')
    elif not 0 < volume < ideal * 0.97:
        raise RuntimeError('Infill did not create internal voids; inspect before export.')
    out = Path(__file__).resolve().parent / 'output'
    out.mkdir(exist_ok=True)
    destination = out / ('gyroid_tray.stl' if args.gyroid else 'desk_tray.stl')
    mesh.save_stl(str(destination))
    print(f'Saved {destination}')
    if args.section:
        cut_mesh = section_view(tray, args.section, args.cut_at).to_mesh()
        cut_path = out / f'{destination.stem}_section_{args.section}.stl'
        cut_mesh.save_stl(str(cut_path))
        print(f'Saved cutaway {cut_path}')
        picopie.show(cut_mesh,
                     title=f'PicoGK — {args.section.upper()} cutaway')
    elif args.view:
        picopie.show(mesh, title='PicoGK learning lab — tray')


if __name__ == '__main__':
    main()
