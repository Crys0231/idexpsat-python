import pandas as pd
import hashlib
import io
import re
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.domain import Cliente, Marca, Veiculo, Compra, Pesquisa

def gerar_hash_compra(tenant_id: str, cliente_id: str, veiculo_id: str, data_compra: str) -> str:
    """Gera um hash único SHA-256 baseado nas chaves primárias e data."""
    raw_string = f"{tenant_id}-{cliente_id}-{veiculo_id}-{data_compra}"
    return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

def processar_csv_compras(db: Session, tenant_id: str, file_bytes: bytes, marca_nome: str, tipo_pesquisa_id: str):
    
    # 1. Lê o arquivo com o separador correto
    df = pd.read_csv(io.BytesIO(file_bytes), sep=';')
    
    # 2. Converte todos os nomes da coluna MODELO para maiúsculas
    if 'MODELO' in df.columns:
        df['MODELO'] = df['MODELO'].astype(str).str.upper()

    df = df.where(pd.notnull(df), None)
    
    data_compra_atual = datetime.utcnow().date()
    inseridos = ignorados = pesquisas_criadas = 0

    for index, row in df.iterrows():
        telefone_raw = str(row.get('TELEFONE', '')).strip()
        placa_raw = str(row.get('PLACA', '')).strip().upper()
        nome_cliente = str(row.get('NOME', '')).strip()
        cidade = str(row.get('CIDADE', '')).strip()
        modelo = str(row.get('MODELO', '')).strip()

        # LIMPEZA DO TELEFONE E PLACA (Remove parênteses, traços e espaços)
        telefone = re.sub(r'\D', '', telefone_raw) # Só deixa números
        placa = re.sub(r'[^A-Z0-9]', '', placa_raw) # Só deixa letras e números

        if not telefone or not placa or telefone == 'None' or placa == 'None':
            ignorados += 1
            continue

        # 1. Cliente
        cliente = db.query(Cliente).filter_by(tenant_id=tenant_id, telefone=telefone).first()
        if not cliente:
            cliente = Cliente(tenant_id=tenant_id, nome=nome_cliente, telefone=telefone, cidade=cidade)
            db.add(cliente)
            db.flush() 

        # 2. Marca
        marca = db.query(Marca).filter_by(tenant_id=tenant_id, nome=marca_nome).first()
        if not marca:
            marca = Marca(tenant_id=tenant_id, nome=marca_nome)
            db.add(marca)
            db.flush()

        # 3. Veículo
        veiculo = db.query(Veiculo).filter_by(tenant_id=tenant_id, placa=placa).first()
        if not veiculo:
            veiculo = Veiculo(tenant_id=tenant_id, cliente_id=cliente.id, marca_id=marca.id, placa=placa, modelo=modelo)
            db.add(veiculo)
            db.flush()

        # 4. Hash (Bloqueia duplicados)
        hash_compra = gerar_hash_compra(tenant_id, str(cliente.id), str(veiculo.id), str(data_compra_atual))
        compra_existente = db.query(Compra).filter_by(tenant_id=tenant_id, hash_compra=hash_compra).first()

        if compra_existente:
            ignorados += 1
            continue

        # 5. Inserção da Compra Oficial
        nova_compra = Compra(
            tenant_id=tenant_id,
            cliente_id=cliente.id,
            veiculo_id=veiculo.id,
            tipo_pesquisa_id=tipo_pesquisa_id,
            data_compra=data_compra_atual,
            hash_compra=hash_compra,
            loja=cidade if cidade and cidade != 'NONE' else "NÃO INFORMADA" 
        )
        db.add(nova_compra)
        db.flush()

        # 6. GERAÇÃO AUTOMÁTICA DA PESQUISA
        nova_pesquisa = Pesquisa(
            tenant_id=tenant_id,
            tipo_pesquisa_id=tipo_pesquisa_id,
            compra_id=nova_compra.id,
            expira_em=datetime.utcnow() + timedelta(days=30)
        )
        db.add(nova_pesquisa)
        
        inseridos += 1
        pesquisas_criadas += 1

    db.commit()

    return {
        "status": "Sucesso",
        "novas_compras_inseridas": inseridos,
        "novas_pesquisas_geradas": pesquisas_criadas,
        "linhas_ignoradas_duplicadas": ignorados
    }