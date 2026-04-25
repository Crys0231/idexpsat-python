from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Importações do nosso projeto
from app.core.config import settings
from app.api.dependencies import get_db
from app.models.domain import User, Tenant

# Inicialização do FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API para o sistema de pesquisas e dashboards"
)

# Configuração de CORS (Essencial para o Streamlit acessar a API no futuro)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, substitua "*" pela URL do seu Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "API Operacional!", 
        "docs_url": "/docs"
    }

# ── ROTA DE TESTE DO BANCO DE DADOS ──────────────────────────────────────────
@app.get("/api/test-db", tags=["Testes"])
def test_db_connection(db: Session = Depends(get_db)):
    """
    Rota para validar a conexão com o Supabase e testar os modelos do SQLAlchemy.
    """
    try:
        # Busca até 5 Tenants, garantindo que o Soft Delete (deleted_at) está funcionando
        tenants = db.query(Tenant).filter(Tenant.deleted_at == None).limit(5).all()
        
        # Busca até 5 Users ativos
        users = db.query(User).filter(User.deleted_at == None).limit(5).all()
        
        return {
            "status": "Conexão com Supabase bem-sucedida! 🚀",
            "tenants_ativos_encontrados": len(tenants),
            "users_ativos_encontrados": len(users),
            "amostra_tenants": [{"id": str(t.id), "nome": t.nome} for t in tenants],
            "amostra_users": [{"id": str(u.id), "email": u.email, "role": u.role} for u in users]
        }
    except Exception as e:
        # Se algo der errado (senha inválida, erro no modelo, etc), ele retorna o erro claro
        raise HTTPException(status_code=500, detail=f"Erro ao conectar com o banco: {str(e)}")



# Importa e registra os roteadores
from app.api.routes import imports, compras, surveys, marcas, clientes
app.include_router(imports.router, prefix="/api/import", tags=["Importações"])
app.include_router(compras.router, prefix="/api/compras", tags=["Compras"])
app.include_router(surveys.router, prefix="/api/surveys", tags=["Pesquisas"])
app.include_router(marcas.router, prefix="/api/marcas", tags=["Marcas"])
app.include_router(clientes.router, prefix="/api/clientes", tags=["Clientes"])