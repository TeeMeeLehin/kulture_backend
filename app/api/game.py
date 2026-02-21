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

@router.post("/attempt", response_model=AttemptResponse)
async def submit_attempt(
    child_id: UUID = Form(...),
    node_id: UUID = Form(...),
    audio_file: Optional[UploadFile] = File(None),
    # Optional text fallback for debugging if needed, but primary is audio
    transcribed_text: Optional[str] = Form(None), 
    parent: Parent = Depends(get_current_parent)
):
    """
    Submits an attempt for a dialogue node.
    Accepts an audio file (multipart/form-data) OR transcribed_text (for dev).
    """
    # Validate Child Access
    validate_child_access(str(child_id), str(parent.id))

    # 1. Fetch the node to get expected response
    res = supabase.table("scenario_nodes").select("expected_response, points_max").eq("id", str(node_id)).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Node not found")
    
    node = res.data[0]
    expected = node['expected_response']
    
    if not expected:
        return {"correct": True, "score": 0, "feedback": "Continue", "match_percentage": 100}

    # 2. Transcription Logic (Stub)
    user_text = ""
    
    if audio_file:
        # Mock STT: For now, if audio is sent, assume it's correct? 
        # Or better: random failure chance? 
        # For simulation flow, we need deterministic success.
        # Let's say: If audio file size > 0, we assume it matches 'expected' (Perfect STT Stub)
        # UNLESS the filename contains "fail".
        if "fail" in audio_file.filename:
            user_text = "wrong answer"
        else:
            user_text = expected # Perfect match simulation
            
        print(f" Received Audio: {audio_file.filename} -> Mock Transcribed: '{user_text}'")
        
    elif transcribed_text:
        user_text = transcribed_text
    else:
        # No input
        pass

    # 3. Logic: Compare text
    # Simple Fuzzy Match
    ratio = fuzz.ratio(user_text.lower(), expected.lower())
    
    score = 0.0
    feedback = "Try again"
    correct = False
    
    if ratio >= 85:
        score = float(node.get('points_max', 1))
        feedback = "Correct"
        correct = True
    elif ratio >= 60:
        score = float(node.get('points_max', 1)) * 0.5
        feedback = "Almost"
        correct = True 
    
    return {
        "correct": correct,
        "score": score,
        "feedback": feedback,
        "match_percentage": ratio,
        "transcription": user_text
    }

@router.post("/complete")
async def complete_scenario(data: ScenarioCompleteRequest, parent: Parent = Depends(get_current_parent)):
    # Validate Child Access
    validate_child_access(str(data.child_id), str(parent.id))

    # Save the attempt
    attempt_data = data.model_dump(mode='json')
    attempt_data['passed'] = data.score_earned >= (data.max_score * 0.7) 

    res = supabase.table("child_scenario_attempts").insert(attempt_data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to save progress")
        
    return {"status": "success", "saved_id": res.data[0]['id']}
    
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
