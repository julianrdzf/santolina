import cloudinary
from dotenv import load_dotenv
import os

load_dotenv()  # carga las variables del .env

cloudinary.config(
    cloudinary_url=os.getenv("CLOUDINARY_URL"),
    secure=True
)