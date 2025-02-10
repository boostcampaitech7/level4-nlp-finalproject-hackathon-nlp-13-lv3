from sqlmodel import SQLModel, Session, create_engine
from app.config import settings

from contextlib import contextmanager

# from sqlalchemy.ext.declarative import declarative_base
# from sqlacodegen.codegen import CodeGenerator
DATABASE_URL = settings.database_url


# SQLite를 사용할 경우 추가적인 연결 옵션 설정
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {
    "keepalives": 1,
    "keepalives_idle": 30,
    "keepalives_interval": 5,
    "keepalives_count": 5
}

# 엔진 생성 (debug 모드 시 SQL 로깅을 활성화할 수 있음)
engine = create_engine(DATABASE_URL, echo=settings.debug,
                       connect_args=connect_args)


@contextmanager
def get_db_session():
    """일반 스크립트에서 사용할 수 있는 세션 컨텍스트 매니저."""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def get_db():
    """
    FastAPI 의존성 주입용 세션 생성 함수.
    세션은 with 구문을 사용하여 자동으로 종료됩니다.
    """
    with Session(engine) as session:
        yield session


def init_db():
    """
    애플리케이션 시작 시 모든 테이블을 생성하기 위한 함수.
    모델을 정의한 후, 해당 함수를 호출하여 테이블이 생성되도록 합니다.
    """
    SQLModel.metadata.create_all(engine)


# Base = declarative_base()
# Base.query = db_session.query_property()

# metadata_obj = MetaData(bind=engine)
# metadata_obj.create_all()
# metadata_obj.reflect()

# outfile = io.open(r'models/model.py', 'w', encoding='utf-8') if r'models/model.py' else sys.stdout
# generator = CodeGenerator(metadata_obj)
# generator.render(outfile)
