from fastapi import FastAPI, status
from fastapi.responses import HTMLResponse

from src.routes.admin import admin
import src.routes.user as UserRoute
import uvicorn


app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def root():
    content = """
        <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body>
            <h1>A simple API for shortening links. Infer from the docs right here \
            <a href=/docs> Docs </a> for more!</h1>
        </body>
    </html> """
    return HTMLResponse(content=content, status_code=status.HTTP_200_OK)


app.include_router(admin)
app.include_router(router=UserRoute.user)



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)