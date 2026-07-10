import os

from dotenv import load_dotenv
from sqlalchemy import create_engine,text

load_dotenv()

engine = create_engine(
    f"mysql+pymysql://{os.getenv('TIDB_USER')}:{os.getenv('TIDB_PASSWORD')}"
    f"@{os.getenv('TIDB_HOST')}:{os.getenv('TIDB_PORT')}/{os.getenv('TIDB_DATABASE')}",
    connect_args={
        "ssl_verify_cert": True,
        "ssl_verify_identity": True,
        "ssl_ca": os.getenv("TIDB_CA"),
    },
    pool_pre_ping=True,
)


with engine.connect() as conn:
    result = conn.execute(text("SELECT NOW();"))
    print(result.fetchone())

print("Connected!")