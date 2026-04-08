import sys
import os
sys.path.append(os.getcwd())
from app.main import app

for route in app.routes:
    print(f"{route.path} [{route.methods if hasattr(route, 'methods') else 'WS'}]")
