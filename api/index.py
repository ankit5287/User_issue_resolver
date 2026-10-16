import os
import sys
import traceback
from pathlib import Path

# Ensure project root directory is on sys.path for Vercel serverless environment
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartroute.settings')

django_application = None
init_error = None

try:
    from django.core.wsgi import get_wsgi_application
    django_application = get_wsgi_application()
except Exception:
    init_error = traceback.format_exc()

def app(environ, start_response):
    if init_error:
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain; charset=utf-8')])
        return [f"Django Initialization Error on Vercel:\n\n{init_error}".encode('utf-8')]
    try:
        return django_application(environ, start_response)
    except Exception:
        err_msg = traceback.format_exc()
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain; charset=utf-8')])
        return [f"Django Runtime Error on Vercel:\n\n{err_msg}".encode('utf-8')]

application = app
