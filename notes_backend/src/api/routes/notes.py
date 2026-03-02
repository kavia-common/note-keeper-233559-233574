from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from src.db import get_db
from src.models import Note, Tag
from src.schemas import NoteCreate, NoteOut, NoteUpdate, NotesListOut, TagListOut, TagOut

router = APIRouter(prefix="/api", tags=["Notes"])


def _normalize_tag(name: str) -> str:
    return name.strip()


def _get_or_create_tags(db: Session, tag_names: List[str]) -> List[Tag]:
    names = [n for n in (_normalize_tag(t) for t in tag_names) if n]
    if not names:
        return []

    existing = db.execute(select(Tag).where(Tag.name.in_(names))).scalars().all()
    existing_by_name = {t.name: t for t in existing}

    result: List[Tag] = []
    for name in names:
        tag = existing_by_name.get(name)
        if tag is None:
            tag = Tag(id=str(uuid.uuid4()), name=name)
            db.add(tag)
            db.flush()  # allocate PK
            existing_by_name[name] = tag
        result.append(tag)

    return result


def _note_to_out(note: Note) -> NoteOut:
    return NoteOut(
        id=note.id,
        title=note.title,
        content=note.content,
        tags=[TagOut(id=t.id, name=t.name) for t in (note.tags or [])],
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.get(
    "/notes",
    response_model=NotesListOut,
    summary="List notes",
    description="List notes, optionally filtering by tag and/or searching title/content.",
    operation_id="list_notes",
)
# PUBLIC_INTERFACE
def list_notes(
    q: Optional[str] = Query(None, description="Search query applied to title and content (ILIKE)."),
    tag: Optional[str] = Query(None, description="Filter notes that contain this tag name."),
    limit: int = Query(50, ge=1, le=200, description="Page size."),
    offset: int = Query(0, ge=0, description="Pagination offset."),
    db: Session = Depends(get_db),
) -> NotesListOut:
    """Return a paginated list of notes with optional search and tag filtering."""
    stmt = select(Note).options(selectinload(Note.tags)).order_by(Note.updated_at.desc())

    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Note.title.ilike(like), Note.content.ilike(like)))

    if tag:
        stmt = stmt.join(Note.tags).where(Tag.name == tag)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    notes = db.execute(stmt.limit(limit).offset(offset)).scalars().all()

    return NotesListOut(items=[_note_to_out(n) for n in notes], total=int(total))


@router.post(
    "/notes",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create note",
    description="Create a note and associate tags by name (tags are created if missing).",
    operation_id="create_note",
)
# PUBLIC_INTERFACE
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> NoteOut:
    """Create a new note."""
    note = Note(id=str(uuid.uuid4()), title=payload.title, content=payload.content)
    note.tags = _get_or_create_tags(db, payload.tags)

    db.add(note)
    db.commit()
    db.refresh(note)
    return _note_to_out(note)


@router.get(
    "/notes/{note_id}",
    response_model=NoteOut,
    summary="Get note",
    description="Fetch a note by id.",
    operation_id="get_note",
)
# PUBLIC_INTERFACE
def get_note(note_id: str, db: Session = Depends(get_db)) -> NoteOut:
    """Get a note by its UUID."""
    note = (
        db.execute(select(Note).where(Note.id == note_id).options(selectinload(Note.tags)))
        .scalars()
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return _note_to_out(note)


@router.put(
    "/notes/{note_id}",
    response_model=NoteOut,
    summary="Update note",
    description="Update a note. If tags are provided, they replace existing tags.",
    operation_id="update_note",
)
# PUBLIC_INTERFACE
def update_note(note_id: str, payload: NoteUpdate, db: Session = Depends(get_db)) -> NoteOut:
    """Update an existing note."""
    note = (
        db.execute(select(Note).where(Note.id == note_id).options(selectinload(Note.tags)))
        .scalars()
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if payload.title is not None:
        note.title = payload.title
    if payload.content is not None:
        note.content = payload.content
    if payload.tags is not None:
        note.tags = _get_or_create_tags(db, payload.tags)

    db.add(note)
    db.commit()
    db.refresh(note)
    return _note_to_out(note)


@router.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete note",
    description="Delete a note by id.",
    operation_id="delete_note",
)
# PUBLIC_INTERFACE
def delete_note(note_id: str, db: Session = Depends(get_db)) -> None:
    """Delete a note."""
    note = db.execute(select(Note).where(Note.id == note_id)).scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return None


@router.get(
    "/tags",
    response_model=TagListOut,
    summary="List tags",
    description="List all tags.",
    operation_id="list_tags",
)
# PUBLIC_INTERFACE
def list_tags(
    limit: int = Query(200, ge=1, le=500, description="Max number of tags to return."),
    offset: int = Query(0, ge=0, description="Pagination offset."),
    db: Session = Depends(get_db),
) -> TagListOut:
    """List tags."""
    total = db.execute(select(func.count()).select_from(Tag)).scalar_one()
    tags = db.execute(select(Tag).order_by(Tag.name.asc()).limit(limit).offset(offset)).scalars().all()
    return TagListOut(items=[TagOut(id=t.id, name=t.name) for t in tags], total=int(total))
