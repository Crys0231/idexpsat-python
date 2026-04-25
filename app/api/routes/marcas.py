from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.models.domain import Marca

router = APIRouter()

@router.get("/")
def listar_marcas(tenant_id: str, db: Session = Depends(get_db)):
    """Busca todas as marcas ativas de um Tenant específico."""
    
    # Busca na tabela Marca, filtrando pelo tenant e garantindo que não foi deletada
    marcas = db.query(Marca).filter(
        Marca.tenant_id == tenant_id,
        Marca.deleted_at.is_(None)
    ).order_by(Marca.nome.asc()).all()
    
    # Retorna uma lista limpa só com ID e Nome
    return [{"id": str(m.id), "nome": m.nome} for m in marcas]