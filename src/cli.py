import os
import sys
from argparse import ArgumentParser
import json
from shutil import copytree, rmtree


def is_pip_installed():

    import SSD.Core
    return not os.path.islink(SSD.Core.__path__[0])


def get_sources():

    import SSD
    site_packages = os.path.dirname(SSD.__path__[0])
    metadata_repo = [f for f in os.listdir(site_packages) if 'SimulationSimpleDatabase' in f and
                     ('.dist-info' in f or '.egg-info' in f)]
    if len(metadata_repo) == 0:
        quit(print("The project does not seem to be properly installed. Try to re-install using 'pip'."))
    elif len(metadata_repo) > 1:
        quit(print("There might be several version of the project, try to clean your site-packages."))
    metadata_repo = metadata_repo.pop(0)
    if 'direct_url.json' not in os.listdir(os.path.join(site_packages, metadata_repo)):
        return None
    with open(os.path.join(site_packages, metadata_repo, 'direct_url.json'), 'r') as file:
        direct_url = json.load(file)
    return direct_url['url'].split('//')[1]


def is_SOFA_installed():

    try:
        import Sofa
    except ImportError:
        return False
    return True


def copy_examples_dir():

    user = input(f"WARNING: The project was installed with pip, examples must be run in a new repository to avoid "
                 f"writing data in your installation of SSD. Allow the creation of this new repository "
                 f"'{os.path.join(os.getcwd(), 'SSD_examples')}' to run examples (use 'SSD --clean' to cleanly"
                 f"remove it afterward) (y/n):")
    if user.lower() not in ['y', 'yes']:
        quit(print("Aborting."))
    import SSD.examples
    copytree(src=SSD.examples.__path__[0],
             dst=os.path.join(os.getcwd(), 'SSD_examples'))


def clean_examples_dir():

    if not os.path.isdir(examples_dir := os.path.join(os.getcwd(), 'SSD_examples')):
        quit(print(f"The directory '{examples_dir}' does not exists."))
    user = input(f"Do you want to remove the repository '{examples_dir}' (y/n):")
    if user.lower() not in ['y', 'yes']:
        quit(print("Aborting."))
    rmtree(examples_dir)


def print_available_examples(examples):

    example_names = sorted(list(examples.keys()))
    example_per_repo = {}
    for example_name in example_names:
        if type(examples[example_name]) == str:
            root, repo = examples[example_name].split('.')[0], examples[example_name].split('.')[1]
        else:
            root, repo = examples[example_name][0].split('.')[0], examples[example_name][0].split('.')[1]
        repo = 'rendering' if repo == 'rendering-offscreen' else repo
        if root not in example_per_repo:
            example_per_repo[root] = {}
        if repo not in example_per_repo[root]:
            example_per_repo[root][repo] = []
        example_per_repo[root][repo].append(example_name)

    description = '\navailable examples:'
    for repo, sub_repos in example_per_repo.items():
        for sub_repo, names in sub_repos.items():
            description += f'\n   {repo}.{sub_repo}: {names}'
    print(description)


def execute_cli():

    description = "Command Line Interface dedicated to SSD examples."
    parser = ArgumentParser(prog='SSD', description=description)
    parser.add_argument('-c', '--clean', help='clean the example repository.', action='store_true')
    parser.add_argument('-g', '--get', help='get the full example repository locally.', action='store_true')
    parser.add_argument('-r', '--run', type=str, help='run one of the demo sessions.', metavar='')
    args = parser.parse_args()

    # Get a copy of the example repository if pip installed from PyPi.org
    if args.get:
        # Installed with dev.py
        if not is_pip_installed():
            quit(print("The project was installed from sources in dev mode, examples will then be run in "
                       "'SSD.examples'."))
        # Installed with pip from sources
        if (source_dir := get_sources()) is not None:
            quit(print(f"The project was installed with pip from sources, examples will then be run in "
                       f"'{os.path.join(source_dir, 'examples')}'."))
        # Installed with pip from PyPi
        copy_examples_dir()
        return

    # Clean the examples repository if pip installed from PyPi.org
    elif args.clean:
        # Installed with dev.py
        if not is_pip_installed():
            quit(print("The project was installed from sources in dev mode, you cannot clean 'SSD.examples'."))
        # Installed with pip from sources
        if (source_dir := get_sources()) is not None:
            quit(print(f"The project was installed with pip from sources, you cannot clean "
                       f"'{os.path.join(source_dir, 'examples')}'."))
        # Installed with pip from PyPi
        clean_examples_dir()
        return

    examples = {'arrows': 'Core.rendering.arrows.py',
                'markers': 'Core.rendering.markers.py',
                'mesh': 'Core.rendering.mesh.py',
                'point_cloud': 'Core.rendering.point_cloud.py',
                'symbols': 'Core.rendering.symbols.py',
                'foreignkey': 'Core.storage.foreignkeyDB.py',
                'reading': 'Core.storage.readingDB.py',
                'signal': 'Core.storage.signalDB.py',
                'updating': 'Core.storage.updatingDB.py',
                'writing': 'Core.storage.writingDB.py',
                'liver': ['SOFA.rendering.record.py', 'SOFA.rendering.replay.py'],
                'caduceus': ['SOFA.rendering-offscreen.record.py', 'SOFA.rendering-offscreen.replay.py'],
                'caduceus_store': 'SOFA.storage.record.py'}

    # Run a demo script
    if (example := args.run) is not None:
        # Check the example name
        if example.lower() not in examples.keys():
            print(f"Unknown demo '{example}'.")
            quit(print_available_examples(examples))
        # Get the example directory
        if not is_pip_installed():
            import SSD.Core
            source_dir = os.readlink(SSD.Core.__path__[0])
            examples_dir = os.path.join(os.path.dirname(os.path.dirname(source_dir)), 'examples')
        elif (source_dir := get_sources()) is not None:
            examples_dir = os.path.join(source_dir, 'examples')
        else:
            if not os.path.isdir(os.path.join(os.getcwd(), 'SSD_examples')):
                print(f"The directory '{os.path.join(os.getcwd(), 'SSD_examples')}' does not exists.")
                copy_examples_dir()
            examples_dir = os.path.join(os.getcwd(), 'SSD_examples')
        root, repo, script, extension = examples[example].split('.')
        os.chdir(os.path.join(examples_dir, root, repo))
        os.system(f'{sys.executable} {script}.{extension}')
        return

    # No command
    else:
        parser.print_help()
        print_available_examples(examples)


if __name__ == '__main__':
    execute_cli()
