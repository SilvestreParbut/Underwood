#!/usr/bin/env bash
# install.sh — Instalador de Underwood desde GitHub
#
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/SilvestreParbut/Underwood/main/underwood_2.6.7/install.sh | sudo bash
#
# Variables opcionales:
#   UNDERWOOD_GITHUB_USER   (default: USUARIO)
#   UNDERWOOD_GITHUB_REPO   (default: underwood)
#   UNDERWOOD_BRANCH        (default: main)

set -euo pipefail

GITHUB_USER="${UNDERWOOD_GITHUB_USER:-SilvestreParbut}"
GITHUB_REPO="${UNDERWOOD_GITHUB_REPO:-Underwood}"
BRANCH="${UNDERWOOD_BRANCH:-main}"
PKG_DIR="underwood_2.6.7"

R='\033[0;31m'; G='\033[0;32m'; Y='\033[1;33m'; N='\033[0m'
info() { printf "${G}[INFO]${N} %s\n" "$*"; }
warn() { printf "${Y}[WARN]${N} %s\n" "$*"; }
err()  { printf "${R}[ERROR]${N} %s\n" "$*" >&2; }

[[ $EUID -eq 0 ]] || { err "Ejecuta con sudo"; exit 1; }

detect_pm() {
    for pm in dnf apt-get zypper pacman; do
        command -v "$pm" >/dev/null 2>&1 && { echo "$pm"; return; }
    done
    echo ""
}
PM="$(detect_pm)"
[[ -z "$PM" ]] && { err "Gestor de paquetes no soportado"; exit 1; }

install_deps() {
    case "$PM" in
        dnf)
            command -v curl >/dev/null 2>&1 || dnf install -y curl
            dnf install -y python3 2>/dev/null || true
            dnf install -y python3-curses 2>/dev/null || true
            ;;
        apt-get)
            command -v curl >/dev/null 2>&1 || { apt-get update; apt-get install -y curl; }
            apt-get install -y python3 python3-curses 2>/dev/null || apt-get install -y python3
            ;;
        zypper)
            command -v curl >/dev/null 2>&1 || zypper -n install curl
            zypper -n install python3 python3-curses 2>/dev/null || true
            ;;
        pacman)
            command -v curl >/dev/null 2>&1 || pacman -Sy --noconfirm curl
            pacman -S --noconfirm --needed python 2>/dev/null || true
            ;;
    esac
}

info "Comprobando dependencias..."
install_deps

command -v libreoffice >/dev/null 2>&1 || \
    warn "libreoffice no instalado (necesario para exportar PDF/docx)"
command -v hunspell >/dev/null 2>&1 || command -v aspell >/dev/null 2>&1 || \
    warn "hunspell/aspell no instalado (necesario para corrector ortográfico)"

TMPDIR="$(mktemp -d -t underwood-install-XXXXXX)"
trap 'rm -rf "$TMPDIR"' EXIT

URL="https://github.com/${GITHUB_USER}/${GITHUB_REPO}/archive/refs/heads/${BRANCH}.tar.gz"
info "Descargando $URL ..."
curl -fsSL "$URL" -o "$TMPDIR/u.tar.gz"
tar -xzf "$TMPDIR/u.tar.gz" -C "$TMPDIR"
SRC="$(find "$TMPDIR" -maxdepth 1 -type d -name 'underwood-*' | head -n1)"
[[ -z "$SRC" ]] && { err "No se pudo extraer el tarball"; exit 1; }

# Localizar la carpeta que contiene usr/share/underwood/underwood.py
if [[ -d "$SRC/$PKG_DIR/usr/share/underwood" ]]; then
    PKG="$SRC/$PKG_DIR"
elif [[ -d "$SRC/usr/share/underwood" ]]; then
    PKG="$SRC"
else
    err "Estructura inesperada del repo (no encuentro usr/share/underwood)"
    exit 1
fi

info "Instalando archivos en /usr ..."
install -d /usr/bin /usr/share/underwood /usr/share/applications \
           /usr/share/pixmaps /usr/share/doc/underwood

if [[ -f "$PKG/usr/share/underwood/underwood.py" ]]; then
    install -m 755 "$PKG/usr/share/underwood/underwood.py" \
        /usr/share/underwood/underwood.py
else
    err "No encuentro underwood.py"; exit 1
fi
[[ -d "$PKG/usr/share/underwood/locale" ]] && \
    cp -a "$PKG/usr/share/underwood/locale" /usr/share/underwood/

if [[ -f "$PKG/usr/bin/underwood" ]]; then
    install -m 755 "$PKG/usr/bin/underwood" /usr/bin/underwood
else
    cat > /usr/bin/underwood <<'EOF'
#!/usr/bin/env python3
import os, sys
os.execv(sys.executable, [sys.executable,
    "/usr/share/underwood/underwood.py"] + sys.argv[1:])
EOF
    chmod 755 /usr/bin/underwood
fi

if compgen -G "$PKG/usr/share/applications/*.desktop" >/dev/null; then
    install -m 644 "$PKG/usr/share/applications/"*.desktop /usr/share/applications/
fi
if compgen -G "$PKG/usr/share/pixmaps/*" >/dev/null; then
    install -m 644 "$PKG/usr/share/pixmaps/"* /usr/share/pixmaps/
fi
[[ -d "$PKG/usr/share/doc" ]] && \
    cp -a "$PKG/usr/share/doc/." /usr/share/doc/underwood/ 2>/dev/null || true

update-desktop-database /usr/share/applications 2>/dev/null || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
    gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true

info "✓ Underwood instalado. Ejecuta: underwood"
