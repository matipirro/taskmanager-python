"""
Tests del CRUD de Task Manager API.
Ejecutar con: pytest -v
"""

from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock

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

    assert response.status_code == 201
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
    assert create_response.status_code == 201
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


# ---------- Tests del endpoint /suggest (Claude API mockeado) ----------

def _mock_claude_response(json_text: str) -> MagicMock:
    """Helper: construye un mock de respuesta de Claude con el texto dado."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json_text)]
    return mock_response


def test_suggest_persiste_subtareas_cuando_claude_responde_ok():
    """Happy path: Claude devuelve JSON válido, endpoint persiste subtasks y devuelve 200."""
    # 1. Crear una task real
    create_response = client.post("/tasks", json={
        "title": "Aprender Docker",
        "description": "Fundamentos de contenedores",
        "completed": False
    })
    task_id = create_response.json()["id"]

    # 2. Mockear la llamada a Claude
    fake_json = '{"subtasks": ["Instalar Docker Desktop", "Crear Dockerfile", "docker build + run"]}'
    with patch("ai_service._client.messages.create", return_value=_mock_claude_response(fake_json)):
        response = client.post(f"/tasks/{task_id}/suggest")

    # 3. Verificar respuesta
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert len(data["subtasks"]) == 3
    titles = [s["title"] for s in data["subtasks"]]
    assert titles == ["Instalar Docker Desktop", "Crear Dockerfile", "docker build + run"]
    # Cada subtask tiene id generado por la BD y task_id apuntando a la task padre
    for subtask in data["subtasks"]:
        assert "id" in subtask
        assert subtask["task_id"] == task_id
        assert subtask["completed"] is False


def test_suggest_devuelve_404_si_task_no_existe():
    """Si la task no existe, devuelve 404 sin llamar a Claude."""
    response = client.post("/tasks/99999/suggest")
    assert response.status_code == 404
    assert "no encontrada" in response.json()["detail"]


def test_suggest_devuelve_502_si_claude_responde_basura():
    """Si Claude devuelve texto no-JSON, endpoint devuelve 502 (Bad Gateway)."""
    # 1. Crear task
    create_response = client.post("/tasks", json={"title": "X", "description": "Y"})
    task_id = create_response.json()["id"]

    # 2. Mockear respuesta inválida (no es JSON)
    bad_response = "Hola, esto no es JSON válido para nada"
    with patch("ai_service._client.messages.create", return_value=_mock_claude_response(bad_response)):
        response = client.post(f"/tasks/{task_id}/suggest")

    # 3. Verificar
    assert response.status_code == 502
    assert "Error de IA" in response.json()["detail"]


# ---------- Tests de endpoints de Subtasks ----------

def test_listar_subtasks_devuelve_lista_persistida():
    """GET /tasks/{id}/subtasks devuelve las subtasks que /suggest persistió."""
    # 1. Crear task
    task_id = client.post("/tasks", json={"title": "Task con subs", "description": "test"}).json()["id"]

    # 2. Suggest (mockeado) → persiste 3 subtasks
    fake_json = '{"subtasks": ["Sub A", "Sub B", "Sub C"]}'
    with patch("ai_service._client.messages.create", return_value=_mock_claude_response(fake_json)):
        client.post(f"/tasks/{task_id}/suggest")

    # 3. Listar las subtasks
    response = client.get(f"/tasks/{task_id}/subtasks")
    assert response.status_code == 200
    subtasks = response.json()
    assert len(subtasks) == 3
    assert [s["title"] for s in subtasks] == ["Sub A", "Sub B", "Sub C"]


def test_listar_subtasks_task_inexistente_devuelve_404():
    response = client.get("/tasks/99999/subtasks")
    assert response.status_code == 404
    assert "no encontrada" in response.json()["detail"]


def test_actualizar_subtask_marca_completada():
    """PUT /subtasks/{id} con completed=true actualiza solo ese campo."""
    # 1. Crear task + suggest para tener una subtask
    task_id = client.post("/tasks", json={"title": "T"}).json()["id"]
    fake_json = '{"subtasks": ["Primera", "Segunda", "Tercera"]}'
    with patch("ai_service._client.messages.create", return_value=_mock_claude_response(fake_json)):
        suggest_resp = client.post(f"/tasks/{task_id}/suggest")
    subtask_id = suggest_resp.json()["subtasks"][0]["id"]

    # 2. Marcar completada
    response = client.put(f"/subtasks/{subtask_id}", json={"completed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == subtask_id
    assert data["completed"] is True
    assert data["title"] == "Primera"  # título intacto (exclude_unset funcionando)


def test_actualizar_subtask_inexistente_devuelve_404():
    response = client.put("/subtasks/99999", json={"completed": True})
    assert response.status_code == 404


def test_actualizar_subtask_sin_campos_devuelve_400():
    """Enviar body vacío debe devolver 400."""
    # Necesitamos una subtask real para que llegue a la validación
    task_id = client.post("/tasks", json={"title": "T"}).json()["id"]
    fake_json = '{"subtasks": ["A", "B", "C"]}'
    with patch("ai_service._client.messages.create", return_value=_mock_claude_response(fake_json)):
        suggest_resp = client.post(f"/tasks/{task_id}/suggest")
    subtask_id = suggest_resp.json()["subtasks"][0]["id"]

    response = client.put(f"/subtasks/{subtask_id}", json={})
    assert response.status_code == 400
    assert "No se enviaron campos" in response.json()["detail"]


def test_cascade_delete_borra_subtasks():
    """Al borrar una Task, sus Subtasks se borran automáticamente (cascade)."""
    # 1. Crear task + suggest
    task_id = client.post("/tasks", json={"title": "Will be deleted"}).json()["id"]
    fake_json = '{"subtasks": ["A", "B", "C"]}'
    with patch("ai_service._client.messages.create", return_value=_mock_claude_response(fake_json)):
        client.post(f"/tasks/{task_id}/suggest")

    # 2. Confirmar que hay 3 subtasks
    assert len(client.get(f"/tasks/{task_id}/subtasks").json()) == 3

    # 3. Borrar la task
    assert client.delete(f"/tasks/{task_id}").status_code == 200

    # 4. GET subtasks de task borrada → 404
    response = client.get(f"/tasks/{task_id}/subtasks")
    assert response.status_code == 404
    
# ---------- Tests de validación Pydantic (422 Unprocessable Entity) ----------

def test_crear_task_sin_title_devuelve_422():
    """Pydantic rechaza el request si falta un campo obligatorio."""
    response = client.post("/tasks", json={"description": "sin title"})
    assert response.status_code == 422


def test_crear_task_con_title_vacio_devuelve_422():
    """Pydantic rechaza title vacío (min_length=1)."""
    response = client.post("/tasks", json={"title": ""})
    assert response.status_code == 422


def test_crear_task_con_title_muy_largo_devuelve_422():
    """Pydantic rechaza title > 200 caracteres."""
    response = client.post("/tasks", json={"title": "x" * 201})
    assert response.status_code == 422


def test_crear_task_con_campo_extra_devuelve_422():
    """extra='forbid' rechaza campos no declarados en el schema."""
    response = client.post("/tasks", json={
        "title": "Test",
        "campo_no_existe": "foo"
    })
    assert response.status_code == 422


def test_actualizar_subtask_con_title_vacio_devuelve_422():
    """SubtaskUpdate también valida title no vacío si se envía."""
    # Primero crear task + suggest para tener una subtask
    task_id = client.post("/tasks", json={"title": "T"}).json()["id"]
    fake_json = '{"subtasks": ["A", "B", "C"]}'
    with patch("ai_service._client.messages.create", return_value=_mock_claude_response(fake_json)):
        suggest_resp = client.post(f"/tasks/{task_id}/suggest")
    subtask_id = suggest_resp.json()["subtasks"][0]["id"]

    # title vacío debe fallar con 422
    response = client.put(f"/subtasks/{subtask_id}", json={"title": ""})
    assert response.status_code == 422