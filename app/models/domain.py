import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Text, Date, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base

# --- Entidades de Acesso ---

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    nome = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    users = relationship("User", back_populates="tenant")
    clientes = relationship("Cliente", back_populates="tenant")

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, default="admin")
    open_id = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="users")

# --- Entidades de Negócio ---

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nome = Column(String)
    telefone = Column(String, nullable=False)
    cidade = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="clientes")
    veiculos = relationship("Veiculo", back_populates="cliente")

class Marca(Base):
    __tablename__ = "marcas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nome = Column(String, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

class Veiculo(Base):
    __tablename__ = "veiculos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"))
    marca_id = Column(UUID(as_uuid=True), ForeignKey("marcas.id"))
    placa = Column(String, nullable=False)
    modelo = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    cliente = relationship("Cliente", back_populates="veiculos")

class TipoPesquisa(Base):
    __tablename__ = "tipos_pesquisa"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nome = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

# --- Entidades de Operação (Compras e Pesquisas) ---

class Compra(Base):
    __tablename__ = "compras"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    veiculo_id = Column(UUID(as_uuid=True), ForeignKey("veiculos.id"), nullable=False)
    tipo_pesquisa_id = Column(UUID(as_uuid=True), ForeignKey("tipos_pesquisa.id"), nullable=False)
    data_compra = Column(Date)
    hash_compra = Column(String, nullable=False, index=True)
    loja = Column(String) 
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

class Pesquisa(Base):
    __tablename__ = "pesquisas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    tipo_pesquisa_id = Column(UUID(as_uuid=True), ForeignKey("tipos_pesquisa.id"), nullable=False)
    compra_id = Column(UUID(as_uuid=True), ForeignKey("compras.id"))
    token = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, server_default=text("uuid_generate_v4()"))
    respondida = Column(Boolean, default=False)
    data_resposta = Column(DateTime)
    
    # Controle de Disparos e Expiração
    enviada = Column(Boolean, default=False)
    data_envio = Column(DateTime, nullable=True)
    expira_em = Column(DateTime, nullable=True)

    # Tratativa de Detratores / RAC
    ligacao_feita = Column(Boolean, default=False)
    ligacao_feita_por = Column(String, nullable=True)
    rac_aberto = Column(Boolean, default=False)
    rac_aberto_por = Column(String, nullable=True)
    tratado = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    respostas = relationship("Resposta", back_populates="pesquisa")

class Pergunta(Base):
    __tablename__ = "perguntas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    tipo_pesquisa_id = Column(UUID(as_uuid=True), ForeignKey("tipos_pesquisa.id"))
    pergunta = Column(Text, nullable=False)
    tipo_pergunta = Column(String, default="scale")
    ordem = Column(Integer)
    ativa = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)


class Resposta(Base):
    __tablename__ = "respostas"
    __table_args__ = (
        UniqueConstraint('pesquisa_id', 'pergunta_id', name='respostas_pesquisa_id_pergunta_id_key'),
    )
    # Verifique se todos esses campos abaixo possuem o "Column(...)"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    pesquisa_id = Column(UUID(as_uuid=True), ForeignKey("pesquisas.id", ondelete="CASCADE"), nullable=False)
    pergunta_id = Column(UUID(as_uuid=True), ForeignKey("perguntas.id"), nullable=False)
    resposta = Column(Text)
    score = Column(Integer)
    sentimento = Column(String, nullable=True)
    temas = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    pesquisa = relationship("Pesquisa", back_populates="respostas")