from typing import Optional
from numpy.random import uniform
from numpy.linalg import norm
from numpy import zeros, array
import Sofa

from SSD.SOFA.Rendering import UserAPI


class Liver(Sofa.Core.Controller):

    def __init__(self, root, factory: Optional[UserAPI] = None, *args, **kwargs):
        Sofa.Core.Controller.__init__(self, *args, **kwargs)

        self.root: Sofa.Core.Node = root
        self.step: int = 0

        # Create the Factory
        self.factory = factory

        # Root
        self.root.dt.value = 0.02
        with open('plugins.txt', 'r') as file:
            required_plugins = [plugin[:-1] if plugin.endswith('\n') else plugin for plugin in file.readlines()
                                if plugin != '\n']
        self.root.addObject('RequiredPlugin', pluginName=required_plugins)
        self.root.addObject('VisualStyle', displayFlags='showVisual')
        self.root.addObject('DefaultAnimationLoop')

        # Liver.Physics
        self.root.addChild('liver')
        self.root.liver.addObject('MeshGmshLoader', name='Liver', filename='mesh/liver.msh')
        self.root.liver.addObject('EulerImplicitSolver', rayleighMass=0.1, rayleighStiffness=0.1)
        self.root.liver.addObject('CGLinearSolver', iterations=25, tolerance=1e-9, threshold=1e-9)
        self.root.liver.addObject('TetrahedronSetTopologyContainer', name='Grid', src='@Liver')
        self.root.liver.addObject('TetrahedronSetGeometryAlgorithms', template='Vec3d')
        self.root.liver.addObject('MechanicalObject', name='GridMO', src='@Liver')
        self.root.liver.addObject('DiagonalMass', massDensity=0.1)
        self.root.liver.addObject('TetrahedralCorotationalFEMForceField', template='Vec3d', method='large',
                                  youngModulus=50000, poissonRatio=0.4, computeGlobalMatrix=False)
        self.root.liver.addObject('FixedProjectiveConstraint', indices=[3, 39, 64])

        # Liver.Surface
        self.root.liver.addChild('surface')
        self.root.liver.surface.addObject('SphereLoader', name='Spheres', filename='mesh/liver.sph')
        self.root.liver.surface.addObject('MechanicalObject', name='SurfaceMO', position='@Spheres.position')
        self.root.liver.surface.addObject('BarycentricMapping', input='@..', output='@.')
        self.cff = self.root.liver.surface.addObject('ConstantForceField', name='CFF', indices=[33],
                                                     forces=[[0., 0., 0.]], showArrowSize=5e-4)

        # Liver.Visual
        self.root.liver.addChild('visual')
        self.root.liver.visual.addObject('MeshOBJLoader', name='Liver', filename='mesh/liver-smooth.obj')
        self.root.liver.visual.addObject('OglModel', name='LiverOgl', src='@Liver')
        self.root.liver.visual.addObject('BarycentricMapping', input='@..', output='@.')

    def onSimulationInitDoneEvent(self, _):

        # Add object to the factory
        if self.factory is not None:
            # Window 1: Liver only (id=0)
            self.factory.add_mesh_callback(position_object='@liver.visual.LiverOgl', cell_type='triangles',
                                           animated=True, at=0, c='red5')

            # Window 2: Liver (id=1) + Force (id=2)
            self.factory.add_mesh_callback(position_object='@liver.visual.LiverOgl', cell_type='triangles',
                                           animated=True, at=1, c='green8', wireframe=True, line_width=1)
            self.factory.add_arrows_callback(position_object='@liver.surface.SurfaceMO',
                                             vector_object='@liver.surface.CFF', start_indices=array([33]),
                                             animated=True, at=1, scale=0.5e-3, c='green3', res=20)

            # Window 3: Grid (id=3 & id=4) + Constraint (id=5)
            self.factory.add_points_callback(position_object='@liver.GridMO', animated=True,
                                             at=2, c='grey3', point_size=8)
            self.factory.add_mesh_callback(position_object='@liver.GridMO', topology_object='@liver.Grid',
                                           cell_type='tetrahedra', animated=True,
                                           at=2, c='grey3', wireframe=True, line_width=1)
            self.factory.add_markers(normal_to=4, indices=array([3, 39, 64]),
                                     at=2, c='red3', size=0.5, symbol='0', filled=False)

            # Window 4: Liver Displacement (id=6)
            nb_points = len(self.root.liver.visual.getObject('LiverOgl').position.value)
            self.factory.add_mesh_callback(position_object='@liver.visual.LiverOgl', cell_type='triangles',
                                           animated=True, at=3, alpha=0.6, colormap='coolwarm',
                                           scalar_field=zeros((nb_points,)))

    def onAnimateBeginEvent(self, _):

        # Change the force value every 50 time steps
        if self.step % 50 == 0:
            f = uniform(-1, 1, (1, 3))
            f = (f / norm(f)) * 5e3
            self.cff.forces.value = f
        self.step += 1

    def onAnimateEndEvent(self, _):

        # Update the non-auto data fields
        if self.factory is not None:
            current = self.root.liver.visual.getObject('LiverOgl')
            init = self.root.liver.visual.getObject('Liver')
            self.factory.update_mesh(object_id=6,
                                     scalar_field=norm(current.position.value - init.position.value, axis=1))
