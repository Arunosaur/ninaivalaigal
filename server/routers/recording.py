"""
Recording Management Router
Extracted from main.py for better code organization
"""

from auth import get_current_user
from auto_recording import get_auto_recorder
from database import DatabaseManager, User
from fastapi import APIRouter, Depends, HTTPException

# Initialize router
router = APIRouter(prefix="/context", tags=["recording"])


# Database manager dependency
def get_db():
    """Get database manager with dynamic configuration"""
    from config import get_dynamic_database_url

    return DatabaseManager(get_dynamic_database_url())


def get_auto_recorder_instance(db: DatabaseManager = Depends(get_db)):
    """Get auto recorder with dynamic database"""
    return get_auto_recorder(db)


@router.post("/start")
async def start_recording(
    context: str,
    current_user: User = Depends(get_current_user),
    auto_recorder=Depends(get_auto_recorder_instance),
):
    """Start CCTV-style automatic recording to a context"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

        # Start automatic CCTV recording
        result = await auto_recorder.start_recording(context, user_id)

        if result["success"]:
            return {
                "message": result["message"],
                "context": context,
                "auto_recording": True,
                "context_id": result.get("context_id"),
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start recording: {str(e)}"
        )


@router.post("/stop")
async def stop_recording(
    context: str = None, current_user: User = Depends(get_current_user)
):
    """Stop CCTV-style automatic recording"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

        if context:
            # Stop specific context recording
            result = await auto_recorder.stop_recording(context)
            if result["success"]:
                return {
                    "message": result["message"],
                    "context": context,
                    "messages_recorded": result.get("messages_recorded", 0),
                }
            else:
                raise HTTPException(status_code=500, detail=result["error"])
        else:
            # Stop all active recordings for user
            status = await auto_recorder.get_recording_status()
            stopped_contexts = []
            for context_name in list(status["contexts"].keys()):
                result = await auto_recorder.stop_recording(context_name)
                if result["success"]:
                    stopped_contexts.append(context_name)

            return {
                "message": f"🛑 Stopped recording for {len(stopped_contexts)} contexts",
                "stopped_contexts": stopped_contexts,
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/status")
async def get_recording_status(current_user: User = Depends(get_current_user)):
    """Get CCTV recording status for all contexts"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

        status = await auto_recorder.get_recording_status()
        return {
            "recording_status": (
                "🎥 CCTV Active"
                if status["active_contexts"] > 0
                else "🔴 CCTV Inactive"
            ),
            "active_contexts": status["active_contexts"],
            "contexts": status["contexts"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get recording status: {str(e)}"
        )


@router.get("/active")
def get_active_recording_context(current_user: User = Depends(get_current_user)):
    """Get active recording context with user isolation (legacy endpoint)"""
    try:
        active_context = db.get_active_context(current_user.id)
        return {"recording_context": active_context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
