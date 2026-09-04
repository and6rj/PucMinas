def criar_tabela(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS precos (
                id SERIAL PRIMARY KEY,
                produto VARCHAR(100) NOT NULL,
                preco NUMERIC(10, 2) NOT NULL
            )
        """)
    conn.commit()


def salvar_preco(conn, produto: str, preco: float):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO precos (produto, preco) VALUES (%s, %s)",
            (produto, preco)
        )
    conn.commit()


def buscar_preco(conn, produto: str) -> float | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT preco FROM precos WHERE produto = %s",
            (produto,)
        )
        resultado = cur.fetchone()
        return float(resultado[0]) if resultado else None
