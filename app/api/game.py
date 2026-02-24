from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from rapidfuzz import fuzz 
from app.db.supabase import supabase
from app.api.deps import get_current_parent, validate_child_access
from app.models.auth import Parent

router = APIRouter()

class AttemptResponse(BaseModel):
    correct: bool
    score: float 
    feedback: str 
    match_percentage: int
    transcription: Optional[str] = None

class ScenarioCompleteRequest(BaseModel):
    child_id: UUID
    scenario_id: UUID
    score_earned: int
    max_score: int
    stars_earned: int 

@router.post("/attempt")
async def submit_scenario_attempt(data: ScenarioCompleteRequest, parent: Parent = Depends(get_current_parent)):
    # Validate Child Access
    validate_child_access(str(data.child_id), str(parent.id))

    # Save the attempt
    attempt_data = data.model_dump(mode='json')
    # Require at least ~60% to pass (e.g., 2 out of 3 questions correct)
    attempt_data['passed'] = data.score_earned >= (data.max_score * 0.6) 

    res = supabase.table("child_scenario_attempts").insert(attempt_data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to save progress")
        
    # Check for level completion and unlock artifacts
    unlocked_artifact = None
    
    if attempt_data['passed']:
        try:
            # 1. Fetch the child's current stats to update them
            child_res = supabase.table("children").select("respect_score, current_level").eq("id", str(data.child_id)).execute()
            if child_res.data:
                child = child_res.data[0]
                new_respect = child.get("respect_score", 0) + data.score_earned
                new_level = child.get("current_level", 1)
                
                # Check level progression
                s_res = supabase.table("scenarios").select("level_id").eq("id", str(data.scenario_id)).execute()
                if s_res.data:
                    level_id = s_res.data[0]['level_id']
                    
                    all_s_res = supabase.table("scenarios").select("id").eq("level_id", level_id).execute()
                    level_scenario_ids = {s['id'] for s in all_s_res.data}
                    
                    passed_res = supabase.table("child_scenario_attempts").select("scenario_id").eq("child_id", str(data.child_id)).eq("passed", True).execute()
                    passed_scenario_ids = {p['scenario_id'] for p in passed_res.data}
                    
                    if level_scenario_ids and level_scenario_ids.issubset(passed_scenario_ids):
                        # Level completely passed! Check for artifact details
                        art_res = supabase.table("artifacts").select("id, name, description, image_url").eq("level_id", level_id).execute()
                        if art_res.data:
                            unlocked_artifact = art_res.data[0]
                            artifact_id = unlocked_artifact['id']
                            has_art = supabase.table("child_artifacts").select("id").eq("child_id", str(data.child_id)).eq("artifact_id", artifact_id).execute()
                            
                            if not has_art.data:
                                try:
                                    supabase.table("child_artifacts").insert({
                                        "child_id": str(data.child_id),
                                        "artifact_id": artifact_id
                                    }).execute()
                                    # Since they just completed this level for the FIRST time and got the artifact, bump their current level
                                    new_level += 1
                                except Exception as e:
                                    print(f"Error unlocking artifact: {e}")
                
                # 2. Save the updated stats to the DB
                supabase.table("children").update({
                    "respect_score": new_respect,
                    "current_level": new_level
                }).eq("id", str(data.child_id)).execute()
                
        except Exception as e:
            print(f"Error updating child stats: {e}")

    return {
        "status": "success", 
        "saved_id": res.data[0]['id'],
        "passed": attempt_data['passed'],
        "unlocked_artifact": unlocked_artifact
    }
    
@router.post("/cards/complete")
async def complete_card(data: dict, parent: Parent = Depends(get_current_parent)):
    # Expects child_id, card_id
    child_id = data.get("child_id")
    card_id = data.get("card_id")
    
    if not child_id or not card_id:
        raise HTTPException(status_code=400, detail="Missing child_id or card_id")
    
    # Validate Child Access
    validate_child_access(str(child_id), str(parent.id))
        
    res = supabase.table("child_action_card_completions").insert({
        "child_id": child_id,
        "card_id": card_id
    }).execute()
    
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to save card completion")
        
    return {"status": "success", "saved_id": res.data[0]['id']}
