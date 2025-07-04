import os

# Caminho absoluto para a raiz do projeto (independente de onde rodar)
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

BASE_DIR = os.path.abspath(os.path.join(SRC_DIR, '..'))

MODELS_DIR = os.path.join(SRC_DIR, 'models')
INTERFACE_DIR = os.path.join(SRC_DIR, 'Interface.py')
DRONE_MODEL_PATH = os.path.join(MODELS_DIR, 'drone.pt')
MAQUETE_MODEL_PATH = os.path.join(MODELS_DIR, 'modelomaquete.pt')

# Pasta para salvar frames de acidentes
OUTPUT_DIR = os.path.join(SRC_DIR, 'data', 'output')
INPUT_DIR = os.path.join(SRC_DIR, 'data', 'input')