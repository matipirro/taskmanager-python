"""Servicio de integración con Claude API para sugerencias de subtareas."""
import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

# Cargar variables desde .env al importar el módulo
load_dotenv()

# Cliente global de Anthropic (se autentica automáticamente con ANTHROPIC_API_KEY)
_client = Anthropic()

# Modelo a usar: Haiku 4.5 (rápido y barato)
MODEL = "claude-haiku-4-5"


def suggest_subtasks(title: str, description: str | None) -> list[str]:
    """
    Dado el título y descripción de una tarea, pide a Claude 3 subtareas.

    Args:
        title: Título de la tarea (obligatorio).
        description: Descripción opcional de la tarea.

    Returns:
        Lista de 3 strings con las subtareas sugeridas.

    Raises:
        ValueError: Si Claude devuelve una respuesta que no es JSON válido.
    """
    prompt = (
        f"Eres un asistente que ayuda a descomponer tareas en subtareas accionables.\n\n"
        f"Tarea:\n"
        f"- Título: {title}\n"
        f"- Descripción: {description or '(sin descripción)'}\n\n"
        f"Genera EXACTAMENTE 3 subtareas concretas y accionables.\n"
        f"Devuelve SOLO un JSON con esta forma exacta, sin texto adicional:\n"
        f'{{"subtasks": ["subtarea 1", "subtarea 2", "subtarea 3"]}}'
    )

    response = _client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    # Claude devuelve texto dentro de response.content[0].text
    text = response.content[0].text.strip()

    # Claude a veces envuelve el JSON en markdown code fences ```json ... ```
    # Los eliminamos si aparecen antes de parsear
    if text.startswith("```"):
        # Quitamos primera línea (```json o ```) y última (```)
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]).strip()

    try:
        data = json.loads(text)
        return data["subtasks"]
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Respuesta inválida de Claude: {text}") from e