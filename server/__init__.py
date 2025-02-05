from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import list_models_app, get_models_app, chat_app, speech_app

def create_app():
	app = FastAPI(title="OpenAI API")
	app.add_middleware(
		CORSMiddleware,
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)
	for i in (list_models_app, get_models_app, chat_app, speech_app):
		app.include_router(i,prefix="/v1")
	return app