from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID

from app.api.dependencies import get_db
from app.models.domain import Pesquisa, Pergunta, Resposta, Compra, Veiculo, TipoPesquisa
from app.schemas.survey_schemas import PesquisaSubmit

router = APIRouter()

@router.get("/{token}")
def carregar_pesquisa(token: UUID, db: Session = Depends(get_db)):
    """Valida o token e retorna os dados da pesquisa + perguntas ativas."""
    
    # SQLAlchemy prefere is_(None) ao invés de == None
    pesquisa = db.query(Pesquisa).filter(Pesquisa.token == token, Pesquisa.deleted_at.is_(None)).first()
    
    if not pesquisa:
        raise HTTPException(status_code=404, detail="Pesquisa não encontrada ou link inválido.")
    
    if pesquisa.respondida:
        raise HTTPException(status_code=400, detail="Esta pesquisa já foi respondida. Muito obrigado!")
    
    if pesquisa.expira_em and datetime.utcnow() > pesquisa.expira_em:
        raise HTTPException(status_code=400, detail="O link desta pesquisa expirou.")

    compra = db.query(Compra).filter_by(id=pesquisa.compra_id).first()
    veiculo = db.query(Veiculo).filter_by(id=compra.veiculo_id).first() if compra else None
    tipo_pesquisa = db.query(TipoPesquisa).filter_by(id=pesquisa.tipo_pesquisa_id).first()

    perguntas = db.query(Pergunta)\
        .filter(
            Pergunta.tipo_pesquisa_id == pesquisa.tipo_pesquisa_id, 
            Pergunta.ativa == True, 
            Pergunta.deleted_at.is_(None)
        )\
        .order_by(Pergunta.ordem.asc())\
        .all()

    return {
        "pesquisa_id": str(pesquisa.id),
        "contexto": {
            "loja": compra.loja if compra else None,
            "veiculo": veiculo.modelo if veiculo else None,
            "tipo": tipo_pesquisa.nome if tipo_pesquisa else "Pesquisa"
        },
        "perguntas": [
            {
                "id": str(p.id),
                "texto": p.pergunta,
                "tipo": p.tipo_pergunta
            } for p in perguntas
        ]
    }

@router.post("/{token}/responder")
def salvar_respostas(token: UUID, payload: PesquisaSubmit, db: Session = Depends(get_db)):
    """Recebe as notas do cliente e salva no banco de dados."""
    
    pesquisa = db.query(Pesquisa).filter(Pesquisa.token == token, Pesquisa.deleted_at.is_(None)).first()
    
    if not pesquisa or pesquisa.respondida or (pesquisa.expira_em and datetime.utcnow() > pesquisa.expira_em):
        raise HTTPException(status_code=400, detail="Link inválido, expirado ou já respondido.")

    for resp in payload.respostas:
        pergunta_existe = db.query(Pergunta).filter(Pergunta.id == resp.pergunta_id).first()
        if not pergunta_existe:
            raise HTTPException(status_code=400, detail=f"A pergunta informada não existe no banco de dados.")
        
        nova_resposta = Resposta(
            tenant_id=pesquisa.tenant_id,
            pesquisa_id=pesquisa.id,
            pergunta_id=resp.pergunta_id,
            score=resp.score,
            resposta=resp.resposta_texto
        )
        db.add(nova_resposta)

    pesquisa.respondida = True
    pesquisa.data_resposta = datetime.utcnow()

    db.commit()

    return {"status": "Sucesso", "mensagem": "Respostas salvas com sucesso! Obrigado."}