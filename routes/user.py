from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from schemas.user import UserCreate
from schemas.url import URLBase
from utils.database_utils import get_db
from utils.router_utils import generate_keys
from utils.qr_utils import generate_qr_code
from utils.snowflake import SnowflakeGenerator, generate_short_code_from_snowflake, base62_encode
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from turtle_link_shortener.models import User as UserModel, URL as URLModel, UserURL
from turtle_link_shortener.security import Password
from turtle_link_shortener.errors import UserNotFound, URLNotValid, URLForwardError
from pydantic import AnyUrl
from pydantic.tools import parse_obj_as
from datetime import datetime
from fastapi.responses import JSONResponse
import io
import base64

user = APIRouter()


@user.post("/user/create", tags=["users"])
async def create_user(new_user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = Password.hash(new_user.password)
    db_user = UserModel(**new_user.model_dump())

    snowflake = SnowflakeGenerator(worker_id=1, datacenter_id=0)
    user_id = snowflake.next_id()

    db_user.password = hashed_password
    db_user.id = user_id

    # sql = text(
    #     "INSERT INTO users (id, username, password, is_admin, is_deleted) VALUES (?, ?, ?, ?)",
    #     [user_id, new_user.username, hashed_password, new_user.is_deleted]
    # )

    # db.execute(
    #     sql
    # )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # result = db.execute("SELECT * FROM users WHERE id = ?", [user_id]).fetchone()
    # db_user = UserModel.from_row(result)

    return db_user


@user.get("/user/{user_id}", tags=["users"])
async def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.get(UserModel, user_id)
    if db_user is None:
        raise UserNotFound(status_code=404, detail=f"No user with id={user_id}")
    return db_user


@user.post("/user/{user_id}/shorten", tags=["users"])
async def shorten_link(
    url: URLBase, user_id: int, custom_key: str, db: Session = Depends(get_db)
):
    if not parse_obj_as(AnyUrl, url.target_url):
        raise URLNotValid(status_code=400, detail="Your provided URL is not valid")

    if db.get(UserModel, user_id) is None:
        raise UserNotFound(status_code=404, 
                detail=f"No user with id={user_id}. Cannot proceed with user_auth!")

    # check if the custom_url has been used by another user
    if db.scalar(select(URLModel).where(URLModel.custom_url == custom_key)) is not None:
        raise URLNotValid(status_code=400, 
                          detail=f"Custom URL {custom_key} \
                          has already been used by another user!")

    # set the characters to be used for tokenization
    key, secret_key = generate_keys(custom_key)
    now = datetime.now()

    # snowflake to generate url_id in distributed systems
    snowflake = SnowflakeGenerator(worker_id=1, datacenter_id=0)
    url_id = snowflake.next_id()

    short_code = base62_encode(url_id)
    # add the generated data to URL Model Table
    db_url = URLModel(id=url_id, target_url=url.target_url, custom_url=short_code, 
                    secret_key=secret_key, time_created=now)

    db_user_url = UserURL(user_id=user_id, link_created=key, link_time_created=now)

    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    
    db.add(db_user_url)
    db.commit()
    db.refresh(db_user_url)

    db_url.custom_url = key
    db_url.admin_url = secret_key
    
    qr_code = generate_qr_code(db_url)

    # Convert the PIL Image to bytes for response.
    img_bytes = io.BytesIO()
    qr_code.save(img_bytes)
    img_bytes = img_bytes.getvalue()

    # Return the short URL and the QR code image in the response.
    response = {
        "short_url": db_url.custom_url,
        "admin_url": db_url.admin_url,
        "qr_code": base64.b64encode(img_bytes).decode('utf-8')
    }

    return JSONResponse(content=response)


@user.get("/{custom_url}", tags=["users"])
async def forward(custom_url: str, db: Session = Depends(get_db)):
    url = db.scalar(select(URLModel).where(URLModel.custom_url == custom_url))

    if url is not None:
        url.clicks += 1
        db.commit()
        db.refresh(url)
        
        return RedirectResponse(url.target_url, status_code=307)
    else:
        raise URLForwardError(status_code=404, 
                detail=f"Bad Request. {custom_url} not linked to any valid url!")


@user.get("/user/{user_id}/links", tags=["users"])
async def get_links(user_id: int, db: Session = Depends(get_db)):
    db_user = db.get(UserModel, user_id)

    if db_user is None:
        raise UserNotFound(status_code=404, detail=f"No user with id={user_id}")
        
    return db_user.links
    