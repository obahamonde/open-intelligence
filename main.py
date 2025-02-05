from dotenv import load_dotenv
from fastapi.responses import RedirectResponse

load_dotenv()
from server import create_app

app = create_app()

@app.get('/')
def redirect_to_docs():
    return RedirectResponse(url='/docs')