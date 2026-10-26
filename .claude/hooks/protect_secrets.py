"""Hook PreToolUse: bloquea cambios a .env y commits con credenciales.

Claude Code le pasa por stdin un JSON con la herramienta y sus parámetros.
exit 0 = permitir, exit 2 = bloquear (el mensaje de stderr le llega a Claude).
"""
import json
import re
import subprocess
import sys
from pathlib import PurePath

# Archivos .env protegidos (.env, .env.local, .env.prod...). .env.example queda permitido
ENV_FILE = re.compile(r"^\.env(\.(?!example$)[\w.-]+)?$")

# Mención de un .env dentro de un comando de shell
ENV_IN_COMMAND = re.compile(r"(?<![\w.-])\.env(?!\.example)(\.[\w.-]+)?(?![\w.-])")

# Operaciones de shell que escriben, borran o mueven archivos (Bash y PowerShell)
WRITE_OPS = re.compile(
    r">|\b(rm|mv|cp|tee|truncate|touch)\b|sed\s+-i|git\s+(add|rm|mv)\b"
    r"|\b(Set-Content|Add-Content|Out-File|Remove-Item|Move-Item|Copy-Item|New-Item|Rename-Item)\b",
    re.IGNORECASE,
)

GIT_COMMIT = re.compile(r"\bgit\s+commit\b")

# Formato de las API keys de Anthropic
SECRET = re.compile(r"sk-ant-[\w-]{20,}")


def block(reason):
    print(f"BLOQUEADO por protect_secrets: {reason}", file=sys.stderr)
    sys.exit(2)


def git_output(args, cwd):
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return result.stdout


def check_file_tool(tool_input):
    path = tool_input.get("file_path", "")
    if ENV_FILE.match(PurePath(path).name):
        block(f"no se puede modificar {path}. Edita el .env a mano.")


def check_command(command, cwd):
    if ENV_IN_COMMAND.search(command) and WRITE_OPS.search(command):
        block("el comando modifica o añade un archivo .env.")

    if GIT_COMMIT.search(command):
        staged = git_output(["diff", "--cached", "--name-only"], cwd).splitlines()
        if any(ENV_FILE.match(PurePath(name).name) for name in staged):
            block("hay un archivo .env en stage.")

        # Lo que está en stage + lo modificado sin stage (cubre git commit -a)
        diff = git_output(["diff", "--cached"], cwd) + git_output(["diff"], cwd)
        added_lines = [line for line in diff.splitlines() if line.startswith("+")]
        if any(SECRET.search(line) for line in added_lines):
            block("el diff contiene algo con forma de API key (sk-ant-...).")


def main():
    sys.stderr.reconfigure(encoding="utf-8")
    data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    cwd = data.get("cwd") or "."

    if tool_name in ("Edit", "Write", "MultiEdit"):
        check_file_tool(tool_input)
    elif tool_name in ("Bash", "PowerShell"):
        check_command(tool_input.get("command", ""), cwd)

    sys.exit(0)


if __name__ == "__main__":
    main()
