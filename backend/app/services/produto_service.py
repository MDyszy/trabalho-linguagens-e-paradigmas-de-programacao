from sqlalchemy.orm import Session
from app.repositories.produto_repository import ProdutoRepository
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.movimentacao_repository import MovimentacaoRepository
from app.schemas.produto import ProdutoCreate
from app.domain.estoque import TipoMovimentacao, em_alerta

produto_repo = ProdutoRepository()
categoria_repo = CategoriaRepository()
movimentacao_repo = MovimentacaoRepository()

class ProdutoService:

    def get_all(self, db: Session):
        return produto_repo.get_all(db)

    def get_by_id(self, db: Session, id: int):
        return produto_repo.get_by_id(db, id)

    def create(self, db: Session, data: ProdutoCreate):
        categoria = categoria_repo.get_by_nome(db, data.categoria_nome)
        if not categoria:
            categoria = categoria_repo.create(db, data.categoria_nome)

        produto_data = data.model_dump(exclude={"categoria_nome", "quantidade"})
        produto_data["categoria_id"] = categoria.id
        produto = produto_repo.create_from_dict(db, produto_data)

        # O estoque inicial vira a 1ª movimentação de entrada (evento imutável).
        if data.quantidade > 0:
            movimentacao_repo.create(
                db, produto.id, TipoMovimentacao.ENTRADA.value, data.quantidade
            )
            db.refresh(produto)
        return produto

    def get_alertas(self, db: Session):
        # Filtro funcional sobre o saldo DERIVADO (não há mais coluna quantidade).
        produtos = produto_repo.get_all(db)
        return [p for p in produtos if em_alerta(p.quantidade, p.estoque_minimo)]

    def seed(self, db: Session):
        # Limpa dados existentes para evitar duplicatas ao seedar
        # Como o banco é pequeno, podemos apenas verificar se já existem produtos cadastrados
        if len(produto_repo.get_all(db)) > 0:
            return {"message": "Banco de dados já contém dados. Seed abortado para evitar duplicidade."}

        # Dados a serem seedados
        seed_data = [
            {
                "nome": "Notebook Gamer X",
                "categoria_nome": "Tecnologia",
                "quantidade": 10,
                "estoque_minimo": 5,
                "imagem_url": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500&q=80",
                "movimentacoes": [
                    {"tipo": TipoMovimentacao.SAIDA, "quantidade": 2}
                ]
            },
            {
                "nome": "Smartphone Pro 15",
                "categoria_nome": "Tecnologia",
                "quantidade": 15,
                "estoque_minimo": 8,
                "imagem_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&q=80",
                "movimentacoes": [
                    {"tipo": TipoMovimentacao.ENTRADA, "quantidade": 5},
                    {"tipo": TipoMovimentacao.SAIDA, "quantidade": 3}
                ]
            },
            {
                "nome": "Arroz Integral 5kg",
                "categoria_nome": "Alimentos",
                "quantidade": 50,
                "estoque_minimo": 20,
                "imagem_url": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=500&q=80",
                "movimentacoes": [
                    {"tipo": TipoMovimentacao.SAIDA, "quantidade": 38}
                ]
            },
            {
                "nome": "Leite Desnatado 1L",
                "categoria_nome": "Alimentos",
                "quantidade": 60,
                "estoque_minimo": 30,
                "imagem_url": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500&q=80",
                "movimentacoes": [
                    {"tipo": TipoMovimentacao.SAIDA, "quantidade": 15}
                ]
            },
            {
                "nome": "Camiseta Algodão Preta",
                "categoria_nome": "Vestuário",
                "quantidade": 30,
                "estoque_minimo": 15,
                "imagem_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500&q=80",
                "movimentacoes": [
                    {"tipo": TipoMovimentacao.SAIDA, "quantidade": 22}
                ]
            },
            {
                "nome": "Martelo de Aço 500g",
                "categoria_nome": "Ferramentas",
                "quantidade": 5,
                "estoque_minimo": 4,
                "imagem_url": "https://images.unsplash.com/photo-1586864387967-d02ef85d93e8?w=500&q=80",
                "movimentacoes": [
                    {"tipo": TipoMovimentacao.SAIDA, "quantidade": 3}
                ]
            }
        ]

        for item in seed_data:
            # Cria produto usando a lógica existente (cria categoria se não existir)
            p_schema = ProdutoCreate(
                nome=item["nome"],
                categoria_nome=item["categoria_nome"],
                quantidade=item["quantidade"],
                estoque_minimo=item["estoque_minimo"],
                imagem_url=item["imagem_url"]
            )
            # Isso cria o produto e a primeira movimentação de ENTRADA (se quantidade > 0)
            produto = self.create(db, p_schema)

            # Cria movimentações adicionais
            for mov in item["movimentacoes"]:
                movimentacao_repo.create(
                    db, produto.id, mov["tipo"].value, mov["quantidade"]
                )
            
            db.refresh(produto)

        return {"message": f"Seed completo! {len(seed_data)} produtos cadastrados com movimentações históricas."}

    def export_inventory_csv(self, db: Session) -> str:
        import io
        import csv
        
        produtos = self.get_all(db)
        output = io.StringIO()
        # Adiciona BOM para que o Excel em português abra com caracteres corretos
        output.write('\ufeff')
        
        writer = csv.writer(output, delimiter=';')
        writer.writerow(["ID", "Nome", "Categoria", "Saldo Atual", "Estoque Mínimo", "Status Alerta"])
        
        for p in produtos:
            alerta = "EM ALERTA" if em_alerta(p.quantidade, p.estoque_minimo) else "NORMAL"
            categoria_nome = p.categoria.nome if p.categoria else "Sem Categoria"
            writer.writerow([p.id, p.nome, categoria_nome, p.quantidade, p.estoque_minimo, alerta])
            
        return output.getvalue()

    def export_product_movements_csv(self, db: Session, produto_id: int) -> str:
        import io
        import csv
        
        produto = self.get_by_id(db, produto_id)
        if not produto:
            return ""
            
        output = io.StringIO()
        output.write('\ufeff')
        
        writer = csv.writer(output, delimiter=';')
        writer.writerow(["ID Movimentação", "Tipo", "Quantidade", "Data"])
        
        movements = movimentacao_repo.get_by_produto(db, produto_id)
        for m in movements:
            # Formata data para algo mais amigável
            data_formatada = m.data.strftime("%d/%m/%Y %H:%M:%S")
            writer.writerow([m.id, m.tipo.upper(), m.quantidade, data_formatada])
            
        return output.getvalue()

