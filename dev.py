from sys import argv
from os import symlink, unlink, mkdir, listdir
from os.path import join, islink, isdir
from shutil import rmtree
from pathlib import Path
from site import USER_SITE


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
        init_file = open(join(USER_SITE, PROJECT, '__init__.py'), 'w')
        init_file.close()

    # Create symbolic links in site-packages for each package
    for package in listdir(root):
        if not islink(join(USER_SITE, PROJECT, package)):
            symlink(src=join(root, package),
                    dst=join(USER_SITE, PROJECT, package))
            print(f"Linked {join(USER_SITE, PROJECT, package)} -> {join(root, package)}")

# Option 2: remove the symbolic links
else:

    if isdir(join(USER_SITE, PROJECT)):
        for package in listdir(join(USER_SITE, PROJECT)):
            if islink(join(USER_SITE, PROJECT, package)):
                unlink(join(USER_SITE, PROJECT, package))
                print(f"Unlinked {join(USER_SITE, PROJECT, package)} -> {join(root, package)}")
        rmtree(join(USER_SITE, PROJECT))
