import mlflow
import mlflow.sklearn
from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

mlflow.set_experiment("wine-classification")

wine = load_wine()
X_train, X_test, y_train, y_test = train_test_split(
    wine.data, wine.target, test_size=0.2, random_state=42
)

# autolog() é CHAMADA DE FUNÇÃO — não é decorador
# Deve ser chamada ANTES do fit()
mlflow.sklearn.autolog()
with mlflow.start_run(run_name="RF-autolog"):
    model = RandomForestClassifier(max_depth=5, n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    # MLflow capturou automaticamente:
    # - Todos os hiperparâmetros do RandomForest
    # - accuracy, f1, precision, recall
    # - Feature importance
    # - Plots de validação cruzada

print("Run concluído. Compare com o RandomForest manual na UI.")
print("Veja quantos parâmetros e métricas extras o autolog capturou.")
