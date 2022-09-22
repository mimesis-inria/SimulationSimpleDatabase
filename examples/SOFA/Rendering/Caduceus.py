import Sofa

from SSD.Generic.Rendering.VedoFactory import VedoFactory


class Caduceus(Sofa.Core.Controller):

    def __init__(self, root, factory=None, *args, **kwargs):
        Sofa.Core.Controller.__init__(self, *args, **kwargs)
        self.root: Sofa.Core.Node = root
        self.factory: VedoFactory = factory
        self.step = 0
        self.create()

    def create(self):

        # Root node
        self.root.gravity.value = [0, -1000, 0]
        self.root.dt.value = 0.04
        required_plugins = ['CImgPlugin', 'SofaOpenglVisual', 'SofaNonUniformFem', 'SofaConstraint', 'SofaLoader',
                            'SofaImplicitOdeSolver', 'SofaMeshCollision', 'SofaSimpleFem']
        self.root.addObject('RequiredPlugin', pluginName=required_plugins)
        self.root.addObject('VisualStyle', displayFlags='showVisual')
        self.root.addObject('FreeMotionAnimationLoop', parallelCollisionDetectionAndFreeMotion=True)
        self.root.addObject('DefaultPipeline', depth=15, verbose=0, draw=0)
        self.root.addObject('BruteForceBroadPhase')
        self.root.addObject('BVHNarrowPhase')
        self.root.addObject('MinProximityIntersection', alarmDistance=1.5, contactDistance=1)
        self.root.addObject('DefaultContactManager', response='FrictionContactConstraint')
        self.root.addObject('LCPConstraintSolver', tolerance=1e-3, maxIt=1000, initial_guess=False, build_lcp=False,
                            printLog=0, mu=0.2)

        # Camera
        self.root.addObject('InteractiveCamera', position=[0, 30, 90], lookAt=[0, 30, 0])
        self.root.addObject('LightManager')
        self.root.addObject('SpotLight', position=[0, 80, 25], direction=[0, -1, -0.8], cutoff=30, exponent=1)
        self.root.addObject('SpotLight', position=[0, 40, 100], direction=[0, 0, -1], cutoff=30, exponent=1)

        # Snake
        self.root.addChild('snake')
        self.root.snake.addObject('MeshOBJLoader', name='Snake', filename='mesh/snake_body.obj')
        self.root.snake.addObject('EulerImplicitSolver', rayleighMass=1, rayleighStiffness=0.03)
        self.root.snake.addObject('CGLinearSolver', iterations=20, tolerance=1e-12, threshold=1e-18,
                                  template='CompressedRowSparseMatrixMat3x3d')
        self.root.snake.addObject('SparseGridRamificationTopology', name='Grid', src='@Snake', n=[4, 12, 3],
                                  nbVirtualFinerLevels=3, finestConnectivity=0)
        self.root.snake.addObject('MechanicalObject', src='@Grid', scale=1, dy=2)
        self.root.snake.addObject('UniformMass', totalMass=1.)
        self.root.snake.addObject('HexahedronFEMForceField', youngModulus=30000, poissonRatio=0.3, method='large',
                                  updateStiffnessMatrix=False)
        self.root.snake.addObject('UncoupledConstraintCorrection', useOdeSolverIntegrationFactors=False)

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

        # Base
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

        if self.factory is not None:

            # Snake elements
            snake_body_ogl = self.root.snake.visual.body.getObject('OglBody')
            self.factory.add_mesh(positions=snake_body_ogl.position.value,
                                  cells=snake_body_ogl.quads.value,
                                  at=0,
                                  c='grey4')
            snake_eye_ogl = self.root.snake.visual.eye.getObject('OglEye')
            self.factory.add_mesh(positions=snake_eye_ogl.position.value,
                                  cells=snake_eye_ogl.quads.value,
                                  at=0,
                                  c='yellow')

            # Base elements
            base_ogl = self.root.base.visual.getObject('OglBase')
            self.factory.add_mesh(positions=base_ogl.position.value,
                                  cells=base_ogl.quads.value,
                                  at=0,
                                  c='orange3')
            self.factory.add_mesh(positions=base_ogl.position.value,
                                  cells=base_ogl.triangles.value,
                                  at=0,
                                  c='orange3')

            # Collision elements
            snake_coll_topo = self.root.snake.collision.getObject('SnakeCollTopo')
            self.factory.add_mesh(positions=snake_coll_topo.position.value,
                                  cells=snake_coll_topo.triangles.value,
                                  at=1,
                                  c='orange7', wireframe=True)
            stick_coll_topo = self.root.base.stick.getObject('StickCollTopo')
            self.factory.add_mesh(positions=stick_coll_topo.position.value,
                                  cells=stick_coll_topo.edges.value,
                                  at=1,
                                  c='orange7', wireframe=True)
            blobs_coll_topo = self.root.base.blobs.getObject('BlobsCollTopo')
            self.factory.add_mesh(positions=blobs_coll_topo.position.value,
                                  cells=blobs_coll_topo.edges.value,
                                  at=1,
                                  c='orange7', wireframe=True)
            stick_coll_topo = self.root.base.stick.getObject('StickCollTopo')
            self.factory.add_mesh(positions=stick_coll_topo.position.value,
                                  cells=stick_coll_topo.triangles.value,
                                  at=1,
                                  c='orange7', wireframe=True)
            foot_coll_topo = self.root.base.foot.getObject('FootCollTopo')
            self.factory.add_mesh(positions=foot_coll_topo.position.value,
                                  cells=foot_coll_topo.triangles.value,
                                  at=1,
                                  c='orange7', wireframe=True)

    def onAnimateEndEvent(self, _):

        if self.step % 2 == 0 and self.factory is not None:

            snake_ogl = self.root.snake.visual.body.getObject('OglBody')
            self.factory.update_mesh(object_id=0,
                                     positions=snake_ogl.position.value)
            snake_eye_ogl = self.root.snake.visual.eye.getObject('OglEye')
            self.factory.update_mesh(object_id=1,
                                     positions=snake_eye_ogl.position.value)
            snake_coll_mo = self.root.snake.collision.getObject('SnakeCollMo')
            self.factory.update_mesh(object_id=4,
                                     positions=snake_coll_mo.position.value)

        self.step += 1
