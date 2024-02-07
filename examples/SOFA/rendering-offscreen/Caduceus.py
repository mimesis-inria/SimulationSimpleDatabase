from typing import Optional
import Sofa

from SSD.SOFA.Rendering import UserAPI


class Caduceus(Sofa.Core.Controller):

    def __init__(self, root, factory: Optional[UserAPI] = None, *args, **kwargs):
        Sofa.Core.Controller.__init__(self, *args, **kwargs)

        self.root: Sofa.Core.Node = root

        # Create the factory
        self.factory = factory

        # Root
        self.root.gravity.value = [0, -1000, 0]
        self.root.dt.value = 0.04
        with open('plugins.txt', 'r') as file:
            required_plugins = [plugin[:-1] if plugin.endswith('\n') else plugin for plugin in file.readlines()
                                if plugin != '\n']
        self.root.addObject('RequiredPlugin', pluginName=required_plugins)
        self.root.addObject('VisualStyle', displayFlags='showVisual')
        self.root.addObject('FreeMotionAnimationLoop', parallelCollisionDetectionAndFreeMotion=True)
        self.root.addObject('CollisionPipeline', depth=15, verbose=0, draw=0)
        self.root.addObject('BruteForceBroadPhase')
        self.root.addObject('BVHNarrowPhase')
        self.root.addObject('MinProximityIntersection', alarmDistance=1.5, contactDistance=1)
        self.root.addObject('CollisionResponse', response='FrictionContactConstraint')
        self.root.addObject('LCPConstraintSolver', tolerance=1e-3, maxIt=1000, initial_guess=False, build_lcp=False,
                            printLog=0, mu=0.2)

        # Camera
        self.root.addObject('InteractiveCamera', position=[0, 30, 90], lookAt=[0, 30, 0])
        self.root.addObject('LightManager')
        self.root.addObject('SpotLight', name='light1', position=[0, 80, 25], direction=[0, -1, -0.8], cutoff=30,
                            exponent=1)
        self.root.addObject('SpotLight', name='light2', position=[0, 40, 100], direction=[0, 0, -1], cutoff=30,
                            exponent=1)

        # Snake.Physics
        self.root.addChild('snake')
        self.root.snake.addObject('MeshOBJLoader', name='Snake', filename='mesh/snake_body.obj')
        self.root.snake.addObject('EulerImplicitSolver', rayleighMass=1, rayleighStiffness=0.03)
        self.root.snake.addObject('MatrixLinearSystem', name='LinearSystem', template='CompressedRowSparseMatrixMat3x3')
        self.root.snake.addObject('CGLinearSolver', iterations=20, tolerance=1e-12, threshold=1e-18,
                                  template='CompressedRowSparseMatrixMat3x3d', linearSystem='@LinearSystem')
        self.root.snake.addObject('SparseGridRamificationTopology', name='Grid', src='@Snake', n=[4, 12, 3],
                                  nbVirtualFinerLevels=3, finestConnectivity=0)
        self.root.snake.addObject('MechanicalObject', name='GridMO', src='@Grid', scale=1, dy=2)
        self.root.snake.addObject('UniformMass', totalMass=1.)
        self.root.snake.addObject('HexahedronFEMForceField', youngModulus=30000, poissonRatio=0.3, method='large',
                                  updateStiffnessMatrix=False)
        self.root.snake.addObject('UncoupledConstraintCorrection', defaultCompliance=184,
                                  useOdeSolverIntegrationFactors=False)

        # Snake.Collision
        self.root.snake.addChild('collision')
        self.root.snake.collision.addObject('MeshOBJLoader', name='SnakeColl', filename='mesh/meca_snake_900tri.obj')
        self.root.snake.collision.addObject('MeshTopology', name='SnakeCollTopo', src='@SnakeColl')
        self.root.snake.collision.addObject('MechanicalObject', name='SnakeCollMo', src='@SnakeColl')
        self.root.snake.collision.addObject('TriangleCollisionModel', selfCollision=False)
        self.root.snake.collision.addObject('LineCollisionModel', selfCollision=False)
        self.root.snake.collision.addObject('PointCollisionModel', selfCollision=False)
        self.root.snake.collision.addObject('BarycentricMapping', input='@..', output='@.')

        # Snake.Visual
        self.root.snake.addChild('visual')
        self.root.snake.visual.addChild('body')
        self.root.snake.visual.body.addObject('MeshOBJLoader', name='SnakeBody', filename='mesh/snake_body.obj')
        self.root.snake.visual.body.addObject('OglModel', name='OglBody', src='@SnakeBody',
                                              texturename='textures/snakeColorMap.png')
        self.root.snake.visual.body.addObject('BarycentricMapping', input='@../..', output='@.')
        self.root.snake.visual.addChild('eye')
        self.root.snake.visual.eye.addObject('MeshOBJLoader', name='SnakeEye', filename='mesh/snake_yellowEye.obj')
        self.root.snake.visual.eye.addObject('OglModel', name='OglEye', src='@SnakeEye')
        self.root.snake.visual.eye.addObject('BarycentricMapping', input='@../..', output='@.')
        self.root.snake.visual.addChild('cornea')
        self.root.snake.visual.cornea.addObject('MeshOBJLoader', name='SnakeCornea', filename='mesh/snake_cornea.obj')
        self.root.snake.visual.cornea.addObject('OglModel', name='OglCornea', src='@SnakeCornea')
        self.root.snake.visual.cornea.addObject('BarycentricMapping', input='@../..', output='@.')

        # Base.Collision
        self.root.addChild('base')
        self.root.base.addChild('stick')
        self.root.base.stick.addObject('MeshOBJLoader', name='Stick', filename='mesh/collision_batons.obj')
        self.root.base.stick.addObject('MeshTopology', name='StickCollTopo', src='@Stick')
        self.root.base.stick.addObject('MechanicalObject', src='@Stick')
        self.root.base.stick.addObject('LineCollisionModel', simulated=False, moving=False)
        self.root.base.stick.addObject('PointCollisionModel', simulated=False, moving=False)
        self.root.base.addChild('blobs')
        self.root.base.blobs.addObject('MeshOBJLoader', name='Blobs', filename='mesh/collision_boules_V3.obj')
        self.root.base.blobs.addObject('MeshTopology', name='BlobsCollTopo', src='@Blobs')
        self.root.base.blobs.addObject('MechanicalObject', src='@Blobs')
        self.root.base.blobs.addObject('TriangleCollisionModel', simulated=False, moving=False)
        self.root.base.blobs.addObject('LineCollisionModel', simulated=False, moving=False)
        self.root.base.blobs.addObject('PointCollisionModel', simulated=False, moving=False)
        self.root.base.addChild('foot')
        self.root.base.foot.addObject('MeshOBJLoader', name='Foot', filename='mesh/collision_pied.obj')
        self.root.base.foot.addObject('MeshTopology', name='FootCollTopo', src='@Foot')
        self.root.base.foot.addObject('MechanicalObject', src='@Foot')
        self.root.base.foot.addObject('TriangleCollisionModel', simulated=False, moving=False)
        self.root.base.foot.addObject('LineCollisionModel', simulated=False, moving=False)
        self.root.base.foot.addObject('PointCollisionModel', simulated=False, moving=False)

        # Base.Visual
        self.root.base.addChild('visual')
        self.root.base.visual.addObject('MeshOBJLoader', name='Base', filename='mesh/SOFA_pod.obj')
        self.root.base.visual.addObject('OglModel', name='OglBase', src='@Base')

    def onSimulationInitDoneEvent(self, _):

        # Add objects to the factory
        if self.factory is not None:

            # Window 1: Snake visual meshes for body (id=0) and eyes (id=1)
            self.factory.add_mesh_callback(position_object='@snake.visual.body.OglBody', cell_type='quads',
                                           animated=True, at=0, c='#93493a')
            self.factory.add_mesh_callback(position_object='@snake.visual.eye.OglEye', cell_type='quads',
                                           animated=True, at=0, c='yellow5')

            # Window 1: Base visual meshes for quads (id=2) and triangles (id=3)
            self.factory.add_mesh_callback(position_object='@base.visual.OglBase', cell_type='quads',
                                           animated=False, at=0, c='orange4')
            self.factory.add_mesh_callback(position_object='@base.visual.OglBase', cell_type='triangles',
                                           animated=False, at=0, c='orange4')

            # Window 2: Snake collision mesh (id=4)
            self.factory.add_mesh_callback(position_object='@snake.collision.SnakeCollMo', animated=True,
                                           topology_object='@snake.collision.SnakeCollTopo', cell_type='triangles',
                                           at=1, c='orange7', wireframe=True, line_width=2)

            # Window 2: Base Collision meshes for stick (id=5), blobs (id=6) and foot (id=7)
            self.factory.add_mesh_callback(position_object='@base.stick.StickCollTopo', cell_type='edges',
                                           animated=False, at=1, c='orange7', wireframe=True, line_width=2)
            self.factory.add_mesh_callback(position_object='@base.blobs.BlobsCollTopo', cell_type='triangles',
                                           animated=False, at=1, c='orange7', wireframe=True, line_width=2)
            self.factory.add_mesh_callback(position_object='@base.foot.FootCollTopo', cell_type='triangles',
                                           animated=False, at=1, c='orange7', wireframe=True, line_width=2)
