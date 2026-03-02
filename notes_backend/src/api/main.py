from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.notes import router as notes_router

openapi_tags = [
    {
        "name": "Health",
        "description": "Health and diagnostics endpoints.",
    },
    {
        "name": "Notes",
        "description": "CRUD and search endpoints for notes and tags.",
    },
]

app = FastAPI(
    title="Note Keeper API",
    description="Backend API for a retro-themed note keeper app (notes, tags, search).",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    # For production, restrict this to your frontend origin(s).
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notes_router)


@app.get("/", tags=["Health"], summary="Health check")
# PUBLIC_INTERFACE
def health_check():
    """Basic health check endpoint used by deployments/monitors."""
    return {"message": "Healthy"}
