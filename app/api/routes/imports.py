from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.services.data_processor import processar_csv_compras
from app.models.domain import Tenant, TipoPesquisa

router = APIRouter()

@router.post("/csv")
async def upload_csv_compras(
    tenant_id: str = Form(...),
    nome_tipo_pesquisa: str = Form(...),
    marca_nome: str = Form(...), 
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="O arquivo deve ser um CSV.")

    tenant = db.query(Tenant).filter_by(id=tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Grupo Andreta não encontrado.")

    tipo_pesquisa = db.query(TipoPesquisa).filter(
        TipoPesquisa.tenant_id == tenant.id,
        TipoPesquisa.nome.ilike(f"%{nome_tipo_pesquisa}%")
    ).first()

    if not tipo_pesquisa:
        raise HTTPException(status_code=400, detail=f"O tipo de pesquisa '{nome_tipo_pesquisa}' não está cadastrado.")

    try:
        contents = await file.read()
        resultado = processar_csv_compras(
            db=db, 
            tenant_id=tenant.id, 
            file_bytes=contents,
            marca_nome=marca_nome.strip().upper(),
            tipo_pesquisa_id=tipo_pesquisa.id
        )
        return resultado

    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")