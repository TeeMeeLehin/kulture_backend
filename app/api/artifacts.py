from fastapi import APIRouter, Depends
from typing import List
from app.api.deps import get_current_child_query
from app.models.content import Artifact
from app.db.supabase import supabase

router = APIRouter()

@router.get("/", response_model=List[Artifact])
def get_child_artifacts(child: dict = Depends(get_current_child_query)):
    """
    Fetch all artifacts unlocked by the specific child.
    """
    child_id = child['id']
    
    # Fetch artifacts for the child
    res = supabase.table("child_artifacts").select("artifacts(*)").eq("child_id", child_id).execute()
    
    if not res.data:
        return []
        
    # Extract the nested artifact objects
    artifacts_data = [item['artifacts'] for item in res.data if item.get('artifacts')]
    
    return [Artifact(**a) for a in artifacts_data]
