import os
import pytest
import psycopg2
from src.repositorio import criar_tabela, salvar_preco, buscar_preco


@pytest.fixture(scope="module")
def conn():
    database_url = os.environ["DATABASE_URL"]
    connection = psycopg2.connect(database_url)
    criar_tabela(connection)
    yield connection
    connection.close()


@pytest.mark.integration
def test_salvar_e_buscar_preco(conn):
    salvar_preco(conn, "notebook", 3500.00)
    resultado = buscar_preco(conn, "notebook")
    assert resultado == 3500.00


@pytest.mark.integration
def test_produto_inexistente_retorna_none(conn):
    resultado = buscar_preco(conn, "produto_que_nao_existe")
    assert resultado is None


@pytest.mark.integration
def test_buscar_preco_apos_multiplos_saves(conn):
    salvar_preco(conn, "mouse", 150.00)
    salvar_preco(conn, "teclado", 250.00)
    assert buscar_preco(conn, "mouse") == 150.00
    assert buscar_preco(conn, "teclado") == 250.00
