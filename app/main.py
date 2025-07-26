from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers import category, products, auth, permission, reviews
from starlette.middleware.sessions import SessionMiddleware
from loguru import logger

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='hn2aw2d2ad2323d234f454u76uji31w2da231yeu23i0hnf')
logger.add("info.log", format="Log: [{extra[log_id]}:{time} - {level} - {message} ", level="INFO", enqueue = True)


@app.middleware("http")
async def log_middleware(request: Request, call_next):
    log_id = str(uuid4())
    with logger.contextualize(log_id=log_id):
        try:
            response = await call_next(request)
            if response.status_code in [401, 402, 403, 404]:
                logger.warning(f"Request to {request.url.path} failed")
            else:
                logger.info('Successfully accessed ' + request.url.path)
        except Exception as ex:
            logger.error(f"Request to {request.url.path} failed: {ex}")
            response = JSONResponse(content={"success": False}, status_code=500)
        return response


@app.get('/')
async def welcome() -> dict:
    return {'message': 'artme lox'}


@app.get('/create/session')
async def session_set(request: Request):
    request.session['my_session'] = '1234'
    return 'ok'


@app.get('/read_session')
async def session_info(request: Request):
    my_var = request.session.get('my_session')
    return my_var


@app.get("/delete_session")
async def session_delete(request: Request):
    my_var = request.session.pop("my_session")
    return my_var


app.include_router(category.router)
app.include_router(products.router)
app.include_router(auth.router)
app.include_router(permission.router)
app.include_router(reviews.router)