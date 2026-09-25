from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.case import Case
from app.models.propagation import PropagationNode, PropagationEdge
from app.services.propagation_service import format_propagation_graph

router = APIRouter(prefix="/api/cases", tags=["Propagation"])

@router.get("/{case_id}/propagation")
def get_case_propagation_graph(case_id: str, db: Session = Depends(get_db)):
    """Get public social media propagation network graph for a case."""
    c = db.query(Case).filter((Case.id == case_id) | (Case.case_number == case_id)).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    nodes = db.query(PropagationNode).filter(PropagationNode.case_id == c.id).all()
    edges = db.query(PropagationEdge).filter(PropagationEdge.case_id == c.id).all()

    return format_propagation_graph(nodes, edges)
