from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from app.core.config import settings
from app.models.auth import Token, Parent
from app.db.supabase import supabase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/google")

async def get_current_parent(token: str = Depends(oauth2_scheme)) -> Parent:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValidationError):
        raise credentials_exception
    
    # Fetch user from Supabase
    response = supabase.table("parents").select("*").eq("id", user_id).execute()
    if not response.data:
        raise credentials_exception
    
    return Parent(**response.data[0])

def validate_child_access(child_id: str, parent_id: str) -> dict:
    """
    Verifies that the child exists and belongs to the parent.
    Returns the child dictionary (including language).
    """
    # Simple query to check ownership
    res = supabase.table("children").select("*").eq("id", child_id).eq("parent_id", parent_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Child profile not found or access denied")
    return res.data[0]

async def get_current_child_query(
    child_id: str, 
    parent: Parent = Depends(get_current_parent)
) -> dict:
    """
    Dependency for GET requests where child_id is a query parameter.
    """
    return validate_child_access(child_id, str(parent.id))
