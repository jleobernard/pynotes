import logging

import uvicorn

# setup loggers
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

from fastapi import FastAPI

from routers import users, notes
from dependencies import get_subs_client

app = FastAPI()

app.include_router(users.router, prefix='/api')
app.include_router(notes.router, prefix='/api')
# get root logger
logger = logging.getLogger(__name__)  # the __name__ resolve to "main" since we are at the root of the project. 


# This will get the root logger since no logger in the configuration has this name.


@app.on_event("startup")
def startup():
    logger.info("Starting up !")
    subs_client = get_subs_client()
    subs_client.load_subs()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
