from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict
from collections import defaultdict
from app.api.deps import get_current_parent
from app.models.auth import Parent
from app.models.profile import ChildCreate, ChildResponse, Child, ParentDashboardResponse, ChildDashboard, ChildProgress
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

@router.get("/parent/dashboard", response_model=ParentDashboardResponse)
def get_parent_dashboard(parent: Parent = Depends(get_current_parent)):
    """
    Returns an aggregated view for the parent, including their account info,
    and a list of all their children along with their gameplay progression stats.
    """
    children_res = supabase.table("children").select("*").eq("parent_id", str(parent.id)).execute()
    children_data = children_res.data or []
    
    dashboard_children = []
    
    for c in children_data:
        # Calculate scenarios passed
        scenarios_res = supabase.table("child_scenario_attempts").select("id").eq("child_id", str(c['id'])).eq("passed", True).execute()
        scenarios_passed = len(scenarios_res.data) if scenarios_res.data else 0
        
        # Calculate artifacts unlocked
        artifacts_res = supabase.table("child_artifacts").select("id").eq("child_id", str(c['id'])).execute()
        artifacts_unlocked = len(artifacts_res.data) if artifacts_res.data else 0
        
        child_obj = Child(**c)
        progress = ChildProgress(scenarios_passed=scenarios_passed, artifacts_unlocked=artifacts_unlocked)
        
        dashboard_children.append(
            ChildDashboard(**child_obj.model_dump(), progress=progress)
        )
        
    return ParentDashboardResponse(
        parent_name=parent.full_name,
        parent_email=parent.email,
        subscription_status="Active (Free Trial (Expires in 7 days))",
        children=dashboard_children
    )
