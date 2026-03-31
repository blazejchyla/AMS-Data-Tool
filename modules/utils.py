import os
import sys

def get_app_data_path():
    """Returns the path to the SMC/AMSDataTool folder in User AppData."""
    if sys.platform == 'win32':
        base = os.environ.get('APPDATA')
    else:
        base = os.path.expanduser('~/.local/share')
        
    path = os.path.join(base, 'SMC', 'AMSDataTool')
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path