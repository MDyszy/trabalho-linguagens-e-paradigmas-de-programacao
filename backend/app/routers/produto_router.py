from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.produto_service import ProdutoService
from app.schemas.produto import ProdutoCreate, ProdutoResponse

router = APIRouter(prefix="/produtos", tags=["produtos"])
service = ProdutoService()

@router.get("/", response_model=list[ProdutoResponse])
def listar(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/alertas", response_model=list[ProdutoResponse])
def alertas(db: Session = Depends(get_db)):
    return service.get_alertas(db)

@router.get("/{id}", response_model=ProdutoResponse)
def buscar(id: int, db: Session = Depends(get_db)):
    produto = service.get_by_id(db, id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@router.post("/", response_model=ProdutoResponse)
def criar(data: ProdutoCreate, db: Session = Depends(get_db)):
    return service.create(db, data)

@router.post("/seed")
def seed_dados(db: Session = Depends(get_db)):
    return service.seed(db)

@router.get("/exportar/inventario")
def exportar_inventario(db: Session = Depends(get_db)):
    csv_content = service.export_inventory_csv(db)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventario.csv"}
    )

@router.get("/{id}/exportar/movimentacoes")
def exportar_movimentacoes(id: int, db: Session = Depends(get_db)):
    csv_content = service.export_product_movements_csv(db, id)
    if not csv_content:
        raise HTTPException(status_code=404, detail="Produto não encontrado ou sem movimentações")
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=movimentacoes_produto_{id}.csv"}
    )
