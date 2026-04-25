from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.api.dependencies import get_db
from app.models.domain import Compra, Cliente, Resposta, Veiculo, TipoPesquisa
from datetime import datetime

router = APIRouter()

@router.get("/listagem-nps")
def listar_clientes_nps(tenant_id: str, db: Session = Depends(get_db)):
    """
    Busca todas as compras e clientes vinculados, trazendo o status da pesquisa
    e as respostas para alimentar o CRM de NPS.
    """
    # Usamos joinedload para trazer os dados relacionados em uma única consulta (mais rápido)
    compras = db.query(Compra).options(
        joinedload(Compra.cliente),
        joinedload(Compra.veiculo),
        joinedload(Compra.tipo_pesquisa),
        joinedload(Compra.respostas)
    ).filter(Compra.tenant_id == tenant_id).order_by(Compra.data_compra.desc()).all()

    resultado = []
    
    for c in compras:
        # Lógica de Status da Pesquisa:
        # Neutro: sem respostas | Negativo: algum 'NÃO' | Positivo: todos 'SIM'
        respostas_lista = [r.valor.upper() for r in c.respostas]
        
        if not respostas_lista:
            status_pesquisa = "NEUTRO"
        elif "NÃO" in respostas_lista or "NAO" in respostas_lista:
            status_pesquisa = "CRÍTICO"
        else:
            status_pesquisa = "POSITIVO"

        resultado.append({
            "id_compra": str(c.id),
            "status": status_pesquisa,
            "data_compra": c.data_compra.strftime("%d/%m/%Y"),
            "marca": c.veiculo.marca if c.veiculo else "N/A",
            "veiculo": c.veiculo.nome if c.veiculo else "N/A",
            "tipo_pesquisa": c.tipo_pesquisa.nome if c.tipo_pesquisa else "N/A",
            "nome_cliente": c.cliente.nome if c.cliente else "N/A",
            "telefone": c.cliente.telefone if c.cliente else "N/A",
            "tratado": c.tratado,
            # Enviamos as perguntas e respostas reais para o detalhamento (setinha)
            "detalhes_respostas": [
                {"pergunta": r.pergunta, "resposta": r.valor} for r in c.respostas
            ]
        })

    return resultado

@router.patch("/{compra_id}/tratar")
def marcar_como_tratado(compra_id: str, db: Session = Depends(get_db)):
    """Atualiza o campo 'tratado' na tabela de compras."""
    compra = db.query(Compra).filter(Compra.id == compra_id).first()
    if not compra:
        raise HTTPException(status_code=404, detail="Compra não encontrada.")
    
    compra.tratado = True
    compra.tratado_em = datetime.utcnow()
    db.commit()
    
    return {"message": "Status atualizado com sucesso!"}