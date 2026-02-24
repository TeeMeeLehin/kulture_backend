from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict
from collections import defaultdict
from app.api.deps import get_current_parent
from app.models.auth import Parent
from app.models.profile import ChildCreate, ChildResponse, Child
from app.db.supabase import supabase

router = APIRouter()

@router.get("/avatars", response_model=Dict[str, Dict[str, List[str]]])
def get_avatar_dictionary():
    """
    Returns a highly efficient nested dictionary of all avatars for O(1) frontend lookup.
    Format: { "yoruba": { "boy": ["url1", "url2"], "girl": ["url3"] }, "twi": ... }
    """
    response = supabase.table("avatars").select("*").execute()
    
    # Build dictionary
    avatar_dict = defaultdict(lambda: defaultdict(list))
    
    for av in response.data:
        lang = av.get("language", "").lower()
        gen = av.get("gender", "").lower()
        url = av.get("image_url")
        if lang and gen and url:
            avatar_dict[lang][gen].append(url)
            
    return dict(avatar_dict)

@router.post("/kids", response_model=dict)
def create_child(child: ChildCreate, parent: Parent = Depends(get_current_parent)):
    child_data = child.model_dump()
    child_data["parent_id"] = str(parent.id)
    
    # We no longer auto-assign; we expect child.avatar_url to be provided
    response = supabase.table("children").insert(child_data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create child profile")
    
    return {"status": "success", "data": response.data[0]}

@router.get("/kids", response_model=List[Child])
def get_child_profiles(parent: Parent = Depends(get_current_parent)):
    response = supabase.table("children").select("*").eq("parent_id", str(parent.id)).execute()
    
    if not response.data:
        return []
        
    return [Child(**item) for item in response.data]
