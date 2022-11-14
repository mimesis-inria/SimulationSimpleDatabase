import os
import sys
from argparse import ArgumentParser

parser = ArgumentParser(prog='demo', description='Specify the name of the demo.')
parser.add_argument('Demo', metavar='demo', type=str, help='Name of the demo to run.')
args = parser.parse_args()

demo = args.Demo
demos = ['caduceus', 'liver']
directory = 'rendering'

if demo not in demos:
    raise ValueError(f"Unknown demo '{demo}', available are {demos}.")
elif demo == 'caduceus':
    directory += '-offscreen'

repo = os.path.join(os.path.dirname(__file__), 'examples', 'SOFA', directory)
os.chdir(repo)

if demo == 'caduceus':
    if not os.path.exists('caduceus.db'):
        print("Recording data in offscreen mode, please wait...")
        os.system(f'{sys.executable} record.py')
    os.system(f'{sys.executable} replay.py')
else:
    if os.path.exists('liver.db'):
        user = input("An existing Database was found for this demo. Replay it (y/n):")
        if user.lower() in ['no', 'n']:
            os.system(f'{sys.executable} record.py')
        else:
            os.system(f'{sys.executable} replay.py')
    else:
        os.system(f'{sys.executable} record.py')
