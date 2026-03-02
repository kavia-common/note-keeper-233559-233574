from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TagOut(BaseModel):
    id: str = Field(..., description="Tag UUID.")
    name: str = Field(..., description="Unique tag name (case-insensitive normalization is recommended client-side).")


class NoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Note title.")
    content: str = Field(..., min_length=1, description="Note body content (plain text).")
    tags: List[str] = Field(default_factory=list, description="List of tag names to associate with this note.")


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Updated title.")
    content: Optional[str] = Field(None, min_length=1, description="Updated content.")
    tags: Optional[List[str]] = Field(None, description="Replace tags with these tag names (full replace).")


class NoteOut(BaseModel):
    id: str = Field(..., description="Note UUID.")
    title: str = Field(..., description="Note title.")
    content: str = Field(..., description="Note content.")
    tags: List[TagOut] = Field(default_factory=list, description="Tags associated with this note.")
    created_at: datetime = Field(..., description="Creation time (UTC).")
    updated_at: datetime = Field(..., description="Last update time (UTC).")


class NotesListOut(BaseModel):
    items: List[NoteOut] = Field(..., description="List of notes.")
    total: int = Field(..., description="Total matching notes (ignoring pagination).")


class TagListOut(BaseModel):
    items: List[TagOut] = Field(..., description="List of tags.")
    total: int = Field(..., description="Total tags.")
