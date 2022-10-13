import logging
import os
from pathlib import Path

import uvicorn

# setup loggers
main_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = Path(main_dir).parent.absolute()
if os.path.exists(f"{main_dir}/logging.conf"):
    logging_conf_file = open(f"{main_dir}/logging.conf", mode="r")
elif os.path.exists(f"{parent_dir}/logging.conf"):
    logging_conf_file = open(f"{parent_dir}/logging.conf", mode="r")
else:
    raise RuntimeError(f"The file logging.conf could not be found in the current directory ({main_dir}) nor in its "
                       f"parent {parent_dir}")
try:
    logging.config.fileConfig(logging_conf_file, disable_existing_loggers=False)
finally:
    logging_conf_file.close()

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
