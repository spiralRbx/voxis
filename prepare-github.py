"""
prepare-github.py - Prepara o repositório Voxis para GitHub.

O que faz:
1. Cria pasta 'build-voxis/' com todos os arquivos que NÃO vão pro GitHub:
   - build.js, document.md, list-effect.md, public.md, effects-time.txt
   - package.json, package-lock.json, build-manifest.json
   - dist/, dist-api/, build/, node_modules/, tmp/, .pytest_cache/
   - page/voxis/ (site completo - deploy separado via ZIP)
   - page/example/
   - cpp/src/realtime_dynamics_wasm.cpp
   - web-test/
   - .zip files
   - api/ não-minificada (fonte original)

2. Substitui api/ pelos scripts minificados (de api/js/)

3. Remove arquivos de build do diretório principal

Uso:
    python prepare-github.py
    python prepare-github.py --dry-run   (mostra o que faria sem mover nada)
"""

import os
import sys
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(ROOT, "build-voxis")

# Arquivos/pastas que vão para build-voxis (não vão pro GitHub)
MOVE_FILES = [
    "build.js",
    "document.md",
    "list-effect.md",
    "public.md",
    "effects-time.txt",
    "package.json",
    "package-lock.json",
    "build-manifest.json",
    ".nojekyll",
]

MOVE_DIRS = [
    "dist",
    "dist-api",
    "build",
    "node_modules",
    "tmp",
    ".pytest_cache",
    os.path.join("page", "voxis"),
    os.path.join("page", "example"),
    "web-test",
]

# Extensões de arquivo para remover da raiz
REMOVE_EXTENSIONS = [".zip"]


def log(msg):
    print(f"  {msg}")


def run(dry_run=False):
    print("=" * 60)
    print("  Voxis - Preparar para GitHub")
    print("=" * 60)
    print()

    if dry_run:
        print("  [MODO DRY-RUN - nada será alterado]\n")

    # --- Passo 1: Criar build-voxis/ ---
    print("[1/5] Criando build-voxis/...")
    if not dry_run:
        os.makedirs(BUILD_DIR, exist_ok=True)

    # Mover arquivos individuais
    for fname in MOVE_FILES:
        src = os.path.join(ROOT, fname)
        if os.path.exists(src):
            dst = os.path.join(BUILD_DIR, fname)
            log(f"{fname} -> build-voxis/{fname}")
            if not dry_run:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)

    # Mover diretórios
    for dname in MOVE_DIRS:
        src = os.path.join(ROOT, dname)
        if os.path.exists(src):
            dst = os.path.join(BUILD_DIR, dname)
            log(f"{dname}/ -> build-voxis/{dname}/")
            if not dry_run:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.move(src, dst)

    # Mover .zip files
    for f in os.listdir(ROOT):
        if any(f.endswith(ext) for ext in REMOVE_EXTENSIONS):
            src = os.path.join(ROOT, f)
            dst = os.path.join(BUILD_DIR, f)
            log(f"{f} -> build-voxis/{f}")
            if not dry_run:
                shutil.move(src, dst)

    # Mover cpp/src/realtime_dynamics_wasm.cpp
    wasm_cpp = os.path.join("cpp", "src", "realtime_dynamics_wasm.cpp")
    src = os.path.join(ROOT, wasm_cpp)
    if os.path.exists(src):
        dst = os.path.join(BUILD_DIR, wasm_cpp)
        log(f"{wasm_cpp} -> build-voxis/{wasm_cpp}")
        if not dry_run:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)

    print()

    # --- Passo 2: Substituir api/ por versão minificada ---
    print("[2/5] Substituindo api/ por versão minificada...")
    api_src = os.path.join(ROOT, "api")
    api_js = os.path.join(api_src, "js")

    if os.path.exists(api_js):
        # Salvar api/ original em build-voxis/
        api_backup = os.path.join(BUILD_DIR, "api-source")
        log(f"api/ (original) -> build-voxis/api-source/")
        if not dry_run:
            if os.path.exists(api_backup):
                shutil.rmtree(api_backup)
            # Copiar tudo exceto js/ para backup
            os.makedirs(api_backup, exist_ok=True)
            for f in os.listdir(api_src):
                if f == "js":
                    continue
                s = os.path.join(api_src, f)
                d = os.path.join(api_backup, f)
                if os.path.isfile(s):
                    shutil.copy2(s, d)

        # Listar arquivos minificados
        minified_files = os.listdir(api_js)
        for f in minified_files:
            log(f"api/js/{f} -> api/{f} (minificado)")

        if not dry_run:
            # Remover arquivos antigos (não-minificados) da api/
            for f in os.listdir(api_src):
                fpath = os.path.join(api_src, f)
                if f == "js":
                    continue
                if os.path.isfile(fpath):
                    os.remove(fpath)

            # Copiar minificados para api/
            for f in minified_files:
                shutil.copy2(
                    os.path.join(api_js, f),
                    os.path.join(api_src, f),
                )

            # Remover pasta js/
            shutil.rmtree(api_js)
    else:
        log("api/js/ não encontrada - pulando")

    print()

    # --- Passo 3: Limpar page/ se vazio ---
    print("[3/5] Limpando diretórios vazios...")
    page_dir = os.path.join(ROOT, "page")
    if os.path.exists(page_dir):
        remaining = os.listdir(page_dir)
        if not remaining:
            log("Removendo page/ (vazio)")
            if not dry_run:
                os.rmdir(page_dir)
        else:
            log(f"page/ ainda tem: {remaining}")

    print()

    # --- Passo 4: Atualizar .gitignore ---
    print("[4/5] Atualizando .gitignore...")
    gitignore_path = os.path.join(ROOT, ".gitignore")
    new_entries = [
        "",
        "# Build artifacts (prepare-github.py)",
        "build-voxis/",
        "dist-api/",
        "*.zip",
        "tmp/",
    ]

    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        additions = []
        for entry in new_entries:
            clean = entry.strip()
            if clean and clean not in content and not clean.startswith("#"):
                additions.append(entry)
            elif clean.startswith("#"):
                if clean not in content:
                    additions.append(entry)

        if additions:
            for a in additions:
                log(f"Adicionando: {a.strip()}")
            if not dry_run:
                with open(gitignore_path, "a", encoding="utf-8") as f:
                    f.write("\n")
                    for entry in new_entries:
                        f.write(entry + "\n")
        else:
            log("Já está atualizado")
    print()

    # --- Passo 5: Resumo ---
    print("[5/5] Resumo")
    print()
    print("  Estrutura para GitHub:")
    github_items = [
        "src/voxis/       - código Python",
        "cpp/              - código C++ (sem realtime_dynamics_wasm.cpp)",
        "api/              - API JS minificada + WASM",
        "tests/            - testes",
        "benchmarks/       - benchmarks",
        "docs/             - documentação",
        ".github/          - CI/CD",
        "README.md         - readme principal",
        "LICENSE           - licença MIT",
        "pyproject.toml    - config do pacote",
        "CMakeLists.txt    - config CMake",
        "Makefile          - comandos de build",
        "MANIFEST.in       - manifest Python",
        "prepare-github.py - este script",
    ]
    for item in github_items:
        log(item)

    print()
    print("  Movido para build-voxis/:")
    build_items = [
        "page/voxis/       - site (deploy separado)",
        "page/example/     - exemplo",
        "web-test/         - app de teste Flask",
        "dist/, dist-api/  - builds compilados",
        "node_modules/     - deps Node",
        "api-source/       - API original não-minificada",
        "build.js, package.json, etc.",
    ]
    for item in build_items:
        log(item)

    print()
    print("  Pronto! Agora pode fazer 'git add . && git commit'")
    print()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    run(dry_run=dry)
