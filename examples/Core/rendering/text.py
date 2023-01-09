from time import sleep

from SSD.Core.Rendering.VedoFactory import VedoFactory
from SSD.Core.Rendering.VedoVisualizer import VedoVisualizer


# 1. Create the rendering and the Factory, bind them to a new Database
visualizer = VedoVisualizer(database_name='text',
                            remove_existing=True)
factory = VedoFactory(database=visualizer.get_database())


# 2. Add objects to the Factory then init the rendering
factory.add_text(content='Static Bold Text',
                 at=0, corner='TM', c='grey', font='Times', size=3., bold=True)
factory.add_text(content='Static Italic Text',
                 at=0, corner='BM', c='green7', font='Courier', size=2., italic=True)
factory.add_text(content='0', at=0)
visualizer.init_visualizer()


# 3. Run a few step
for step in range(50):
    factory.update_text(object_id=2, content=f'{step}')
    visualizer.render()
    sleep(0.05)
