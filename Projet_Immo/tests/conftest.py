import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "src"))
os.chdir(RACINE)  # les chemins du projet (data/raw, config/) sont relatifs à la racine
