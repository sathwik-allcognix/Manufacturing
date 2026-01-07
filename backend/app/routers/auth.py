from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..security import verify_password, get_password_hash, create_access_token, decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.OrganizationRead)
def register_organization(org_in: schemas.OrganizationCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(models.Organization)
        .filter(models.Organization.org_name == org_in.org_name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Organization name already registered")

    org = models.Organization(
        org_name=org_in.org_name,
        industry_type=org_in.industry_type,
        address=org_in.address,
        password_hash=get_password_hash(org_in.password),
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    # We treat `username` as `org_name`
    org = (
        db.query(models.Organization)
        .filter(models.Organization.org_name == form_data.username)
        .first()
    )
    if not org or not verify_password(form_data.password, org.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect organization name or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": str(org.org_id)})
    return {"access_token": access_token, "token_type": "bearer", "org_id": org.org_id, "org_name": org.org_name}


def get_current_org(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> models.Organization:
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    org_id = int(payload["sub"])
    org = db.query(models.Organization).filter(models.Organization.org_id == org_id).first()
    if not org:
        raise HTTPException(status_code=401, detail="Organization not found")
    return org


