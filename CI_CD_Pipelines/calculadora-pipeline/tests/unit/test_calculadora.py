import pytest
from src.calculadora import calcular_desconto, calcular_imposto, calcular_preco_final


@pytest.mark.unit
class TestCalcularDesconto:
    def test_desconto_normal(self):
        assert calcular_desconto(100.0, 10) == 90.0

    def test_desconto_zero(self):
        assert calcular_desconto(100.0, 0) == 100.0

    def test_desconto_total(self):
        assert calcular_desconto(100.0, 100) == 0.0

    def test_desconto_percentual_negativo(self):
        with pytest.raises(ValueError, match="entre 0 e 100"):
            calcular_desconto(100.0, -5)

    def test_desconto_percentual_acima_de_100(self):
        with pytest.raises(ValueError):
            calcular_desconto(100.0, 110)


@pytest.mark.unit
class TestCalcularImposto:
    def test_imposto_normal(self):
        assert calcular_imposto(100.0, 15) == 15.0

    def test_imposto_zero(self):
        assert calcular_imposto(100.0, 0) == 0.0

    def test_aliquota_negativa(self):
        with pytest.raises(ValueError, match="negativa"):
            calcular_imposto(100.0, -1)


@pytest.mark.unit
class TestCalcularPrecoFinal:
    def test_preco_final_completo(self):
        # 100 - 10% desconto = 90; 90 + 10% imposto = 99
        assert calcular_preco_final(100.0, 10, 10) == 99.0

    def test_sem_desconto_sem_imposto(self):
        assert calcular_preco_final(200.0, 0, 0) == 200.0
