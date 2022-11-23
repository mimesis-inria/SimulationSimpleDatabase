from sys import argv
from os import symlink, unlink, mkdir, listdir, remove, sep
from os.path import join, islink, isdir, isfile
from shutil import rmtree, which
from pathlib import Path
from site import USER_SITE
from pip._internal.operations.install.wheel import PipScriptMaker
from pip._internal.locations import get_scheme


# Package information
PROJECT = 'SSD'
root = join(Path(__file__).parent.absolute(), 'src')

# Check user entry
if len(argv) == 2 and argv[1] not in ['set', 'del']:
    raise ValueError(f"\nInvalid script option."
                     f"\nRun 'python3 dev.py set' to link {PROJECT} to your site package folder."
                     f"\nRun 'python3 dev.py del' to remove {PROJECT} link from your site package folder.")

# Option 1: create the symbolic links
if len(argv) == 1 or argv[1] == 'set':

    # Create the main repository in site-packages
    if not isdir(join(USER_SITE, PROJECT)):
        mkdir(join(USER_SITE, PROJECT))

    # Create symbolic links in site-packages for each package
    for package in [p for p in listdir(root) if isdir(join(root, p)) and p != '__pycache__']:
        if not islink(join(USER_SITE, PROJECT, package)):
            symlink(src=join(root, package),
                    dst=join(USER_SITE, PROJECT, package))
            print(f"Linked {join(USER_SITE, PROJECT, package)} -> {join(root, package)}")

    # Add examples and the CLI script
    if not isdir(join(USER_SITE, PROJECT, 'examples')):
        symlink(src=join(Path(__file__).parent.absolute(), 'examples'),
                dst=join(USER_SITE, PROJECT, 'examples'))
        print(f"Linked {join(USER_SITE, PROJECT, 'examples')} -> {join(Path(__file__).parent.absolute(), 'examples')}")
    if not isfile(join(USER_SITE, PROJECT, 'cli.py')):
        symlink(src=join(root, 'cli.py'),
                dst=join(USER_SITE, PROJECT, 'cli.py'))

    # Create the CLI
    if which('SSD') is None:
        # Generate the scripts
        scheme = get_scheme('SSD', user=True)
        maker = PipScriptMaker(None, scheme.scripts)
        generated_scripts = maker.make_multiple(['SSD = SSD.cli:execute_cli'])
        scripts = [script.split(sep)[-1] for script in generated_scripts]
        for script in generated_scripts:
            if script.split(sep)[-1] != 'SSD':
                remove(script)

# Option 2: remove the symbolic links
else:

    if isdir(join(USER_SITE, PROJECT)):
        for package in listdir(join(USER_SITE, PROJECT)):
            if islink(join(USER_SITE, PROJECT, package)):
                unlink(join(USER_SITE, PROJECT, package))
                print(f"Unlinked {join(USER_SITE, PROJECT, package)} -> {join(root, package)}")
            elif isfile(join(USER_SITE, PROJECT, package)):
                remove(join(USER_SITE, PROJECT, package))
            elif isdir(join(USER_SITE, PROJECT, package)):
                rmtree(join(USER_SITE, PROJECT, package))
        rmtree(join(USER_SITE, PROJECT))
        remove(which('SSD'))
