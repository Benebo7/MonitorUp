
from fastapi import APIRouter, Depends
from security import checkuser
from database import get_session, Cadastro
from sqlmodel import select


router = APIRouter(prefix="/calc", tags=["Calculadora"], dependencies=[Depends(checkuser)])

@router.post("/protected-route")
def calculator(id: str = Depends(checkuser), n1: float = 0, n2: float = 0, session = Depends(get_session)):

    statement = select(Cadastro).where(Cadastro.id == id)
    register = session.exec(statement).first()   
    data = register
    calc = n1 + n2
    return {
            "usuario_autorizado": data.user,
            "resultado": calc
           }
