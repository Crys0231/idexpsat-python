from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

# Molde de uma resposta individual
class RespostaItem(BaseModel):
    pergunta_id: UUID
    score: Optional[int] = Field(default=None, ge=0, le=10, description="Nota de 0 a 10")
    resposta_texto: Optional[str] = None

# Molde do pacote completo que o cliente envia ao clicar em "Finalizar"
class PesquisaSubmit(BaseModel):
    respostas: List[RespostaItem]