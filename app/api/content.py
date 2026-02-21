from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from app.api.deps import get_current_parent, get_current_child_query
from app.models.auth import Parent
from app.models.content import Module, Level, ScenarioDetail, Scenario, DialogueNode
from app.db.supabase import supabase

router = APIRouter()

@router.get("/modules", response_model=List[Module])
def get_modules(child: dict = Depends(get_current_child_query)):
    """
    Fetch all modules for a specific child (based on their language).
    Calculates locked/unlocked status for levels.
    """
    language = child['language'].lower()
    child_id = child['id']
    
    # 1. Fetch Modules with Levels (Join)
    response = supabase.table("modules").select("*, levels(*)").eq("language", language).order("order_index").execute()
    if not response.data:
        return []

    # 2. Fetch Child's Completed Scenarios
    attempts_res = supabase.table("child_scenario_attempts").select("scenario_id").eq("child_id", child_id).eq("passed", True).execute()
    passed_scenario_ids = {a['scenario_id'] for a in attempts_res.data}

    modules = []
    
    for m_data in response.data:
        # Sort levels by order_index
        if 'levels' in m_data:
            m_data['levels'].sort(key=lambda x: x['order_index'])
        
        previous_level_completed = True # First level is always available
        
        for level in m_data.get('levels', []):
            # Fetch scenarios for this level to check completion
            # (Optimized: we could have fetched this in step 1 with nested join if supabase supports deep nesting easily, 
            # but select('*, levels(*, scenarios(id))') might work. For now, separate query is safer for Pydantic mapping).
            
            scenarios_res = supabase.table("scenarios").select("id").eq("level_id", level['id']).execute()
            level_scenario_ids = {s['id'] for s in scenarios_res.data}
            
            is_completed = False
            if level_scenario_ids:
                is_completed = level_scenario_ids.issubset(passed_scenario_ids)
            
            if is_completed:
                level['status'] = 'completed'
                previous_level_completed = True
            elif previous_level_completed:
                level['status'] = 'available'
                previous_level_completed = False 
            else:
                level['status'] = 'locked'
                previous_level_completed = False
        
        modules.append(Module(**m_data))
        
    return modules

@router.get("/levels/{level_id}", response_model=Level)
def get_level_details(level_id: UUID, parent: Parent = Depends(get_current_parent)):
    """
    Fetch specific level details including its scenarios.
    """
    l_res = supabase.table("levels").select("*").eq("id", str(level_id)).execute()
    if not l_res.data:
        raise HTTPException(status_code=404, detail="Level not found")
    
    level = Level(**l_res.data[0])
    
    # Fetch Scenarios
    s_res = supabase.table("scenarios").select("*").eq("level_id", str(level_id)).order("order_index").execute()
    level.scenarios = [Scenario(**s) for s in s_res.data]
    
    return level

@router.get("/scenarios/{scenario_id}/play", response_model=ScenarioDetail)
def get_scenario_play_data(scenario_id: UUID, parent: Parent = Depends(get_current_parent)):
    """
    Fetch the full script (nodes) for a scenario to play it.
    """
    s_res = supabase.table("scenarios").select("*").eq("id", str(scenario_id)).execute()
    if not s_res.data:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    scenario = ScenarioDetail(**s_res.data[0])
    
    # Fetch Dialogue Nodes
    n_res = supabase.table("scenario_nodes").select("*").eq("scenario_id", str(scenario_id)).order("order_index").execute()
    scenario.nodes = [DialogueNode(**n) for n in n_res.data]
    
    return scenario
