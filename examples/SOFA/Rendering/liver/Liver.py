from typing import Optional
from numpy.random import uniform, randint
from numpy.linalg import norm
from numpy import zeros
import Sofa

from SSD.SOFA.Rendering.VedoFactory import VedoFactory


class Liver(Sofa.Core.Controller):

    def __init__(self, root, factory=None, *args, **kwargs):
        Sofa.Core.Controller.__init__(self, *args, **kwargs)

        self.root: Sofa.Core.Node = root
        self.factory: Optional[VedoFactory] = factory
        self.step: int = 0
        self.cff = None

        # Root
        self.root.dt.value = 0.02
        required_plugins = ['SofaOpenglVisual', 'SofaImplicitOdeSolver', 'SofaLoader', 'SofaGeneralSimpleFem',
                            'SofaBoundaryCondition', 'SofaGeneralLoader', 'SofaBaseLinearSolver', 'SofaBaseMechanics']
        self.root.addObject('RequiredPlugin', pluginName=required_plugins)
        self.root.addObject('VisualStyle', displayFlags='showVisual, showWireFrame')
        self.root.addObject('DefaultPipeline', verbose=0)
        self.root.addObject('BruteForceBroadPhase')
        self.root.addObject('BVHNarrowPhase')
        self.root.addObject('DiscreteIntersection')
        self.root.addObject('DefaultContactManager')

        # Liver.Physics
        self.root.addChild('liver')
        self.root.liver.addObject('MeshGmshLoader', name='Liver', filename='mesh/liver.msh')
        self.root.liver.addObject('EulerImplicitSolver', rayleighMass=0.1, rayleighStiffness=0.1)
        self.root.liver.addObject('CGLinearSolver', iterations=25, tolerance=1e-9, threshold=1e-9)
        self.root.liver.addObject('TetrahedronSetTopologyContainer', name='Grid', src='@Liver')
        self.root.liver.addObject('TetrahedronSetGeometryAlgorithms', template='Vec3d')
        self.root.liver.addObject('MechanicalObject', name='GridMO', src='@Liver')
        self.root.liver.addObject('DiagonalMass', massDensity=1.)
        self.root.liver.addObject('TetrahedralCorotationalFEMForceField', template='Vec3d', method='large',
                                  youngModulus=50000, poissonRatio=0.4, computeGlobalMatrix=False)
        self.root.liver.addObject('FixedConstraint', indices=[3, 39, 64])

        # Liver.Surface
        self.root.liver.addChild('surface')
        self.root.liver.surface.addObject('SphereLoader', name='Spheres', filename='mesh/liver.sph')
        self.root.liver.surface.addObject('MechanicalObject', name='SurfaceMO', position='@Spheres.position')
        self.root.liver.surface.addObject('SphereCollisionModel', listRadius='@Spheres.listRadius')
        self.root.liver.surface.addObject('BarycentricMapping', input='@..', output='@.')
        self.cff = self.root.liver.surface.addObject('ConstantForceField', indices=[33], force=[0., 0., 0.],
                                                     showArrowSize=5e-4)

        # Liver.Visual
        self.root.liver.addChild('visual')
        self.root.liver.visual.addObject('MeshOBJLoader', name='Liver', filename='mesh/liver-smooth.obj')
        self.root.liver.visual.addObject('OglModel', name='LiverOgl', src='@Liver')
        self.root.liver.visual.addObject('BarycentricMapping', input='@..', output='@.')

    def onSimulationInitDoneEvent(self, _):

        if self.factory is not None:

            # Window 1: Liver only
            self.factory.add_mesh(record_object=self.root.liver.visual.getObject('LiverOgl'),
                                  cell_type='triangles', animated=True,
                                  at=0, c='red5')

            # Window 2: Liver + Force
            self.factory.add_mesh(record_object=self.root.liver.visual.getObject('LiverOgl'),
                                  cell_type='triangles', animated=True,
                                  at=1, c='red5', wireframe=True, line_width=2)

            # Window 3: Grid + Constraint
            self.factory.add_points(record_object=self.root.liver.getObject('GridMO'), animated=True,
                                    at=2, c='grey3', point_size=10)
            self.factory.add_mesh(topology_object=self.root.liver.getObject('Grid'), cell_type='tetrahedra',
                                  record_object=self.root.liver.getObject('GridMO'), animated=True,
                                  at=2, c='grey3', wireframe=True, line_width=1)

            # Window 4: Liver + Displacement
            nb_points = len(self.root.liver.visual.getObject('LiverOgl').position.value)
            self.factory.add_mesh(record_object=self.root.liver.visual.getObject('LiverOgl'),
                                  cell_type='triangles', animated=True,
                                  at=3, alpha=0.6, colormap='cool', scalar_field=zeros((nb_points,)))

    def onAnimateBeginEvent(self, _):

        if self.step % 50 == 0:
            f = uniform(-1, 1, (3,))
            f = (f / norm(f)) * 5e3
            self.cff.force.value = f
        self.step += 1

    def onAnimateEndEvent(self, _):

        if self.factory is not None:
            current = self.root.liver.visual.getObject('LiverOgl')
            init = self.root.liver.visual.getObject('Liver')
            U = norm(current.position.value - init.position.value, axis=1)
            self.factory.update_mesh(object_id=4, scalar_field=U)