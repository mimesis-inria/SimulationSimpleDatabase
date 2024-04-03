from os import listdir, chdir, getcwd, readlink
from os.path import join, dirname, abspath, exists, isdir, islink
from sys import executable
from json import load
from subprocess import run
from platform import system
from shutil import copytree, rmtree
from argparse import ArgumentParser


def is_pip_installed():

    import SSD.Core
    return not islink(SSD.Core.__path__[0])


def get_sources():

    import SSD
    site_packages = dirname(SSD.__path__[0])
    metadata_repo = [f for f in listdir(site_packages) if 'SimulationSimpleDatabase' in f and
                     ('.dist-info' in f or '.egg-info' in f)]
    if len(metadata_repo) == 0:
        quit(print("The project does not seem to be properly installed. Try to re-install using 'pip'."))
    elif len(metadata_repo) > 1:
        quit(print("There might be several version of the project, try to clean your site-packages."))
    metadata_repo = metadata_repo.pop(0)
    if 'direct_url.json' not in listdir(join(site_packages, metadata_repo)):
        return None
    with open(join(site_packages, metadata_repo, 'direct_url.json'), 'r') as file:
        direct_url = load(file)
    if system() == 'Linux':
        return abspath(direct_url['url'].split('//')[1])
    elif system() == 'Windows':
        return abspath(direct_url['url'].split('///')[1])
    else:
        return abspath(direct_url['url'].split('///')[1])


def is_SOFA_installed():

    try:
        import Sofa
    except ImportError:
        return False
    return True


def copy_examples_dir():

    user = input(f"WARNING: The project was installed with pip, examples must be run in a new repository to avoid "
                 f"writing data in your installation of SSD. Allow the creation of this new repository "
                 f"'{join(getcwd(), 'SSD_examples')}' to run examples (use 'SSD --clean' to cleanly"
                 f"remove it afterward) (y/n):")
    if user.lower() not in ['y', 'yes']:
        quit(print("Aborting."))
    import SSD.examples
    copytree(src=SSD.examples.__path__[0],
             dst=join(getcwd(), 'SSD_examples'))


def clean_examples_dir():

    if not isdir(examples_dir := join(getcwd(), 'SSD_examples')):
        quit(print(f"The directory '{examples_dir}' does not exists."))
    user = input(f"Do you want to remove the repository '{examples_dir}' (y/n):")
    if user.lower() not in ['y', 'yes']:
        quit(print("Aborting."))
    rmtree(examples_dir)


def print_available_examples(examples):

    example_names = sorted(list(examples.keys()))
    example_per_repo = {}
    for example_name in example_names:
        if isinstance(type(examples[example_name]), str):
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
    parser.add_argument('-g', '--get', help='get the full example repository locally.', action='store_true')
    parser.add_argument('-c', '--clean', help='clean the example repository.', action='store_true')
    parser.add_argument('-r', '--run', type=str, help='run one of the demo sessions.', metavar='')
    backends = ['vedo', 'open3d']
    parser.add_argument('-b', '--backend', type=str, help=f'specify the visualization backend among {backends}',
                        metavar='')
    args = parser.parse_args()

    # Get a copy of the example repository if pip installed from PyPi.org
    if args.get:
        # Installed with setup_dev.py
        if not is_pip_installed():
            quit(print("The project was installed from sources in dev mode, examples will then be run in "
                       "'SSD.examples'."))
        # Installed with pip from sources
        if (source_dir := get_sources()) is not None:
            quit(print(f"The project was installed with pip from sources, examples will then be run in "
                       f"'{join(source_dir, 'examples')}'."))
        # Installed with pip from PyPi
        copy_examples_dir()
        return

    # Clean the examples repository if pip installed from PyPi.org
    elif args.clean:
        # Installed with setup_dev.py
        if not is_pip_installed():
            quit(print("The project was installed from sources in dev mode, you cannot clean 'SSD.examples'."))
        # Installed with pip from sources
        if (source_dir := get_sources()) is not None:
            quit(print(f"The project was installed with pip from sources, you cannot clean "
                       f"'{join(source_dir, 'examples')}'."))
        # Installed with pip from PyPi
        clean_examples_dir()
        return

    examples = {'write': 'Core.storage.write_db.py',
                'read': 'Core.storage.read_db.py',
                'update': 'Core.storage.update_db.py',
                'signal': 'Core.storage.signal_db.py',
                'foreignkey': 'Core.storage.foreignkey_db.py',

                'visualization': 'Core.rendering.visualization.py',
                'replay': 'Core.rendering.replay.py',
                'offscreen': 'Core.rendering.offscreen.py',

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
            source_dir = readlink(SSD.Core.__path__[0])
            examples_dir = join(dirname(dirname(source_dir)), 'examples')
        elif (source_dir := get_sources()) is not None:
            examples_dir = join(source_dir, 'examples')
        else:
            if not isdir(join(getcwd(), 'SSD_examples')):
                print(f"The directory '{join(getcwd(), 'SSD_examples')}' does not exists.")
                copy_examples_dir()
            examples_dir = join(getcwd(), 'SSD_examples')

        # Get the backend
        visualizer = []
        if (backend := args.backend) is not None:
            if backend.lower() not in backends:
                raise ValueError(f"The backend '{backend}' is not available. Must be in {backends}")
            visualizer.append(backend.lower())

        # Run the example
        if isinstance(examples[example], str):
            root, repo, script, _ = examples[example].split('.')
            # Check SOFA installation
            if root == 'SOFA' and not is_SOFA_installed():
                quit(print(f"SOFA bindings were not found, unable to run {example} example "
                           f"({join(root, repo, script)}.py)"))
            # Run example
            run([f'{executable}', f'{script}.py'] + visualizer, cwd=join(examples_dir, root, repo))
        else:
            root, repo, example_record, extension = examples[example][0].split('.')
            _, _, example_replay, _ = examples[example][1].split('.')
            # Check SOFA installation
            if root == 'SOFA' and not is_SOFA_installed():
                quit(print(f"SOFA bindings were not found, unable to run {example} example "
                           f"({join(root, repo, example_record)}.py)"))
            chdir(join(examples_dir, root, repo))
            # Get user input between record and replay
            if example == 'caduceus':
                if not exists('caduceus.db'):
                    print("Recording data in offscreen mode, please wait...")
                    run([f'{executable}', f'{example_record}.py'] + visualizer, cwd=join(examples_dir, root, repo))
                run([f'{executable}', f'{example_replay}.py'], cwd=join(examples_dir, root, repo))
            else:
                if exists('liver.db'):
                    user = input("An existing Database was found for this demo. Replay it (y/n):")
                    if user.lower() in ['no', 'n']:
                        run([f'{executable}', f'{example_record}.py'] + visualizer, cwd=join(examples_dir, root, repo))
                    else:
                        run([f'{executable}', f'{example_replay}.py'] + visualizer, cwd=join(examples_dir, root, repo))
                else:
                    run([f'{executable}', f'{example_record}.py'] + visualizer, cwd=join(examples_dir, root, repo))

    # No command
    else:
        parser.print_help()
        print_available_examples(examples)


if __name__ == '__main__':
    execute_cli()
