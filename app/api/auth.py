from fastapi import APIRouter, HTTPException, status, Depends
import requests
from app.core.config import settings
from app.models.auth import GoogleAuthRequest, Token, Parent, UserLogin, UserSignup
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.supabase import supabase
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

router = APIRouter()

@router.post("/signup", response_model=Token)
def signup(user: UserSignup):
    """
    Create a new parent account with Email/Password.
    """
    # 1. Check if email exists
    res = supabase.table("parents").select("id").eq("email", user.email).execute()
    if res.data:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 2. Hash Password
    hashed_pwd = get_password_hash(user.password)
    
    # 3. Create Parent
    parent_data = {
        "email": user.email,
        "full_name": user.full_name,
        "password_hash": hashed_pwd
    }
    res = supabase.table("parents").insert(parent_data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create account")
    
    parent = res.data[0]
    
    # 4. Create Token
    access_token = create_access_token(subject=parent['id'])
    return {"access_token": access_token, "token_type": "bearer", "parent": parent}

@router.post("/login", response_model=Token)
def login(user: UserLogin):
    """
    Login with Email/Password.
    """
    # 1. Fetch Parent
    res = supabase.table("parents").select("*").eq("email", user.email).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    parent = res.data[0]
    
    # 2. Verify Password
    if not parent.get('password_hash'):
        raise HTTPException(status_code=400, detail="Account uses Google Login. Please sign in with Google.")
        
    if not verify_password(user.password, parent['password_hash']):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # 3. Create Token
    access_token = create_access_token(subject=parent['id'])
    return {"access_token": access_token, "token_type": "bearer", "parent": parent}

@router.post("/auth/google", response_model=Token)
def login_google(request: GoogleAuthRequest):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": request.code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": "postmessage",
        "grant_type": "authorization_code"
    }
    
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        tokens = response.json()
        
        # Verify ID token
        id_info = id_token.verify_oauth2_token(
            tokens['id_token'], 
            google_requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        
        email = id_info['email']
        name = id_info.get('name')
        google_id = id_info['sub']
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Google Code or verification failed: {str(e)}"
        )

    # Check if user exists in Supabase
    user_query = supabase.table("parents").select("*").eq("email", email).execute()
    
    if user_query.data:
        parent = Parent(**user_query.data[0])
        # Update google_id if missing (Account Linking)
        if not parent.google_id:
            supabase.table("parents").update({"google_id": google_id}).eq("id", str(parent.id)).execute()
            parent.google_id = google_id
    else:
        # Create new parent
        new_parent_data = {
            "email": email,
            "full_name": name,
            "google_id": google_id
        }
        create_response = supabase.table("parents").insert(new_parent_data).execute()
        if not create_response.data:
             raise HTTPException(status_code=500, detail="Failed to create user")
        parent = Parent(**create_response.data[0])

    # Generate JWT
    access_token = create_access_token(subject=parent.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "parent": parent
    }
