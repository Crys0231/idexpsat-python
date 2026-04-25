from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.models.domain import Compra, Cliente, Veiculo, TipoPesquisa, Tenant

router = APIRouter()

@router.get("/")
def listar_compras(
    tenant_id: str, 
    limit: int = 50, 
    db: Session = Depends(get_db)
):
    """
    Busca as compras mais recentes de um Tenant, trazendo os dados do Cliente, Veículo e Loja.
    """
    # Verifica se o tenant existe
    tenant = db.query(Tenant).filter_by(id=tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado.")

    # Fazendo o JOIN das 4 tabelas para trazer os dados formatados
    resultados = db.query(Compra, Cliente, Veiculo, TipoPesquisa)\
        .join(Cliente, Compra.cliente_id == Cliente.id)\
        .join(Veiculo, Compra.veiculo_id == Veiculo.id)\
        .join(TipoPesquisa, Compra.tipo_pesquisa_id == TipoPesquisa.id)\
        .filter(
            Compra.tenant_id == tenant_id, 
            Compra.deleted_at == None  # Ignora os deletados (Soft Delete)
        )\
        .order_by(Compra.created_at.desc())\
        .limit(limit).all()

    # Formatando o JSON de saída
    compras_formatadas = []
    for compra, cliente, veiculo, tipo in resultados:
        compras_formatadas.append({
            "id_compra": str(compra.id),
            "data": compra.data_compra,
            "loja": compra.loja,
            "tipo_servico": tipo.nome,
            "cliente": {
                "nome": cliente.nome,
                "telefone": cliente.telefone,
                "cidade": cliente.cidade
            },
            "veiculo": {
                "placa": veiculo.placa,
                "modelo": veiculo.modelo
            }
        })

    return {
        "total_exibido": len(compras_formatadas),
        "dados": compras_formatadas
    }