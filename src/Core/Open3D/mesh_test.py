import open3d as o3d
import vedo
import numpy as np
import time

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

# Load the file
armadillo_vedo = vedo.Mesh('armadillo.obj')
liver_vedo = vedo.Mesh('liver.obj').scale(0.01)

# Create the Armadillo
armadillo = o3d.geometry.TriangleMesh(vertices=o3d.utility.Vector3dVector(armadillo_vedo.points()),
                                      triangles=o3d.utility.Vector3iVector(armadillo_vedo.cells()))
armadillo.compute_vertex_normals()
# armadillo.paint_uniform_color(np.array([0.2, 0.5, 0.9, 0.5]))
armadillo_mat = o3d.visualization.rendering.MaterialRecord()
armadillo_mat.shader = "defaultLitTransparency"
armadillo_mat.base_color = np.array([1, 1, 1, 0.8])

# Create the Liver
liver = o3d.geometry.TriangleMesh(vertices=o3d.utility.Vector3dVector(liver_vedo.points()),
                                  triangles=o3d.utility.Vector3iVector(liver_vedo.cells()))
liver.compute_vertex_normals()

cmap_norm = Normalize(vmin=min(np.asarray(armadillo.vertices)[:, -1]),
                      vmax=max(np.asarray(armadillo.vertices)[:, -1]))
pts_color = plt.get_cmap('jet')(cmap_norm(np.asarray(armadillo.vertices)[:, -1]))[:, 0:3]
armadillo.vertex_colors = o3d.utility.Vector3dVector(pts_color)


# Visualization
o3d.visualization.draw([{'name': 'armadillo', 'geometry': armadillo, 'material': armadillo_mat},
                        {'name': 'liver', 'geometry': liver}],
                       non_blocking_and_return_uid=True)
for _ in range(2000):
    time.sleep(0.01)

    # Update the positions


    if not o3d.visualization.gui.Application.instance.run_one_tick():
        break
print('end visu')

