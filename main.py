from dotenv import load_dotenv
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()
from server import create_app

static = StaticFiles(directory="web/dist", html=True)
app = create_app()

@app.get("/v1")
def redirect_to_docs():
    return RedirectResponse(url="/docs")

app.mount("/", static)
