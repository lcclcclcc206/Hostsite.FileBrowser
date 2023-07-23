from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routers import dirs, tokens

app = FastAPI()

app.include_router(dirs.router)
app.include_router(tokens.router)

origins = [
    '*',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=6166, log_level='error')
