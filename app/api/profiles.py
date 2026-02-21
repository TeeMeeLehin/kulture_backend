from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.api.deps import get_current_parent
from app.models.auth import Parent
from app.models.profile import ChildCreate, ChildResponse, Child
from app.db.supabase import supabase

router = APIRouter()

@router.post("/kids", response_model=dict)
def create_child(child: ChildCreate, parent: Parent = Depends(get_current_parent)):
    child_data = child.model_dump()
    child_data["parent_id"] = str(parent.id)
    
    # Auto-Assign Avatar
    # Logic: Fetch avatar URL from avatars table where language & gender match
    # If no match, use a default fallback
    
    av_res = supabase.table("avatars").select("image_url").eq("language", child.language.lower()).eq("gender", child.gender.lower()).execute()
    
    if av_res.data:
        child_data["avatar_url"] = av_res.data[0]["image_url"]
    else:
        # Fallback URL or Generic
        child_data["avatar_url"] = "https://api.dicebear.com/7.x/adventurer/svg?seed=Genercic"

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
