#!/usr/bin/env bash
# scripts/cli_runner.sh — automação local do fluxo Texto → Compilação → Artefatos.
#
# Uso: scripts/cli_runner.sh <etapa> [instancia]
#   build     data/*.yaml → artifacts/ (relatório, quantitativos, quality-report, manifest) + cad/gen/params.scad
#   cad       OpenSCAD → cad/render/modelo.{off,stl,png}; OFF → OBJ (Sweet Home 3D)
#   sh3d      cad/sh3d/Home.xml + modelo.obj → cad/render/modelo.sh3d
#   photo     foto headless do .sh3d via ConsolePhotoGenerator (Java) — ver função
#   manifest  reescreve artifacts/manifest.json enxergando os artefatos do CAD
#   all       build → cad → sh3d → manifest
#   clean     remove artifacts/, cad/render/, cad/gen/
#
# Variáveis: OPENSCAD (binário), SH3D_JAR_DIR (pasta com SweetHome3D-*.jar e libs), UV (padrão: uv).
set -euo pipefail

ETAPA="${1:-all}"
INSTANCIA="${2:-examples/eco-house-demo}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

UV="${UV:-uv}"
OPENSCAD="${OPENSCAD:-openscad}"
CAD="$INSTANCIA/cad"
RENDER="$CAD/render"

log()  { printf '\033[1;34m▶ %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 2; }
warn() { printf '\033[1;33m⚠ %s\033[0m\n' "$*" >&2; }
need() { command -v "$1" >/dev/null 2>&1 || die "ferramenta ausente: $1 — $2"; }

# Etapa 1 — o motor Python. Falha (exit 1) se o perfil de qualidade tiver `fail`.
run_build() {
    log "build: $INSTANCIA"
    "$UV" run arch-engine build "$INSTANCIA"
}

# Etapa 2 — OpenSCAD. O estável (2021.01) exporta OFF/STL/PNG; OBJ vem da conversão (ADR-002).
run_cad() {
    need "$OPENSCAD" "instale o OpenSCAD (apt install openscad) ou aponte OPENSCAD=/caminho"
    [[ -f "$CAD/gen/params.scad" ]] || "$UV" run arch-engine scad-params "$INSTANCIA"
    mkdir -p "$RENDER"
    log "cad: $($OPENSCAD --version 2>&1 | head -1)"
    "$OPENSCAD" -o "$RENDER/modelo.off" "$CAD/main.scad"
    "$OPENSCAD" -o "$RENDER/modelo.stl" "$CAD/main.scad"
    # PNG precisa de contexto OpenGL; sem DISPLAY (CI), roda sob xvfb. Sem nenhum dos dois, pula.
    local png=("$OPENSCAD" -o "$RENDER/modelo.png" --render --viewall --autocenter
               --imgsize=1600,1200 --colorscheme=Tomorrow "$CAD/main.scad")
    if [[ -n "${DISPLAY:-}" ]]; then "${png[@]}"
    elif command -v xvfb-run >/dev/null 2>&1; then xvfb-run -a "${png[@]}"
    else warn "PNG pulado: sem DISPLAY nem xvfb-run (apt install xvfb)"; fi
    "$UV" run arch-engine off2obj "$RENDER/modelo.off" "$RENDER/modelo.obj"
}

# Etapa 3 — Sweet Home 3D como texto: o .sh3d é um zip com Home.xml + o OBJ (ADR-003).
run_sh3d() {
    log "sh3d: empacotando Home.xml + modelo.obj"
    "$UV" run arch-engine pack-sh3d "$INSTANCIA"
}

# Etapa 4 (opcional) — foto fotorrealista headless do .sh3d.
#
# O Sweet Home 3D NÃO tem um flag oficial `-headless`: a GUI aceita `-open arquivo.sh3d`,
# e ponto. O que existe para automação é a classe utilitária `ConsolePhotoGenerator`
# (fonte do SH3D, publicada no fórum do autor), que renderiza com o SunFlow sem GPU
# quando o Java 3D é desligado com `-Dj3d.rend=noop`. Só níveis 3/4 (iluminação global).
#
# Planta humanizada em PDF: só pela GUI (Arquivo › Imprimir em PDF) ou por plugin —
# não há caminho headless verificado. Ver docs/adr/ADR-003 e docs/references.md.
#
# Exemplo verificado (adapte versões e caminhos; SH3D_JAR_DIR = pasta com os jars):
run_photo() {
    need java "instale um JRE 17+ (ex.: sdkman)"
    [[ -n "${SH3D_JAR_DIR:-}" ]] || die "defina SH3D_JAR_DIR com SweetHome3D-*.jar, sunflow-*.jar, j3dcore.jar, vecmath.jar, j3dutils.jar, batik-svgpathparser-*.jar"
    local cp
    cp="$(ls "$SH3D_JAR_DIR"/*.jar | tr '\n' ':')"
    log "photo: ConsolePhotoGenerator (SunFlow, sem GPU)"
    # java -Xmx4g -Dj3d.rend=noop -cp "$cp" \
    #   com.eteks.sweethome3d.utilities.ConsolePhotoGenerator "$RENDER/modelo.sh3d" "$RENDER/foto.png"
    java -Xmx4g -Dj3d.rend=noop -cp "$cp" \
        com.eteks.sweethome3d.utilities.ConsolePhotoGenerator "$RENDER/modelo.sh3d" "$RENDER/foto.png"
}

run_manifest() {
    log "manifest: artifact:v1"
    "$UV" run arch-engine manifest "$INSTANCIA"
}

run_clean() {
    log "clean: artefatos de $INSTANCIA"
    rm -rf "$INSTANCIA/artifacts" "$RENDER" "$CAD/gen"
}

case "$ETAPA" in
    build)    run_build ;;
    cad)      run_cad ;;
    sh3d)     run_sh3d ;;
    photo)    run_photo ;;
    manifest) run_manifest ;;
    all)      run_build; run_cad; run_sh3d; run_manifest ;;
    clean)    run_clean ;;
    *)        sed -n '2,14p' "$0"; exit 64 ;;
esac
