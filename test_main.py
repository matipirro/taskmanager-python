"""
Tests del CRUD de Task Manager API.
Ejecutar con: pytest -v
"""

from fastapi.testclient import TestClient
from main import app

# TestClient es como MockMvc de Spring: simula peticiones HTTP sin arrancar el servidor real
client = TestClient(app)


# ---------- Tests de endpoints básicos ----------

def test_home_devuelve_mensaje_de_bienvenida():
    response = client.get("/")
    assert response.status_code == 200
    assert "Task Manager" in response.json()["mensaje"]


def test_health_devuelve_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------- Tests del CRUD de tasks ----------

def test_crear_task_devuelve_201_con_id():
    payload = {
        "title": "Test task",
        "description": "Esto es un test automático",
        "completed": False
    }
    response = client.post("/tasks", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test task"
    assert data["completed"] is False
    assert "id" in data
    assert isinstance(data["id"], int)


def test_listar_tasks_devuelve_lista():
    response = client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_obtener_task_inexistente_devuelve_404():
    response = client.get("/tasks/99999")
    assert response.status_code == 404
    assert "no encontrada" in response.json()["detail"]


def test_actualizar_task_inexistente_devuelve_404():
    payload = {"title": "X", "description": "Y", "completed": True}
    response = client.put("/tasks/99999", json=payload)
    assert response.status_code == 404


def test_borrar_task_inexistente_devuelve_404():
    response = client.delete("/tasks/99999")
    assert response.status_code == 404


def test_flujo_completo_crud():
    """
    Test de integración: crear -> obtener -> actualizar -> borrar.
    Esto es equivalente a un test @SpringBootTest con MockMvc en Java.
    """
    # 1. Crear
    payload = {"title": "Flujo CRUD", "description": "test integración", "completed": False}
    create_response = client.post("/tasks", json=payload)
    assert create_response.status_code == 200
    task_id = create_response.json()["id"]

    # 2. Obtener
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Flujo CRUD"

    # 3. Actualizar
    update_payload = {"title": "Flujo CRUD", "description": "modificado", "completed": True}
    put_response = client.put(f"/tasks/{task_id}", json=update_payload)
    assert put_response.status_code == 200
    assert put_response.json()["completed"] is True

    # 4. Borrar
    delete_response = client.delete(f"/tasks/{task_id}")
    assert delete_response.status_code == 200

    # 5. Verificar que ya no existe
    verify_response = client.get(f"/tasks/{task_id}")
    assert verify_response.status_code == 404