# Underwood

Procesador de texto minimalista para la terminal, diseñado para escritura creativa: novelas, cuentos, ensayos y guiones.

## Estructura del repositorio

Cada carpeta `underwood_X.Y.Z/` contiene el árbol de empaquetado Debian completo para esa versión:

- `DEBIAN/` — metadatos de instalación (`control`, `postinst`)
- `usr/` — archivos que se instalan en el sistema (`/usr/bin`, `/usr/share`)

## Construcción del paquete `.deb`

Desde la raíz del repositorio:

    dpkg-deb --build --root-owner-group underwood_X.Y.Z underwood_X.Y.Z_all.deb

Sustituye `X.Y.Z` por la versión que quieras empaquetar.

## Instalación

    sudo apt install ./underwood_X.Y.Z_all.deb

## Dependencias

Python 3.8+, xterm, fuente DejaVu, hunspell (con diccionarios ES y EN), xclip.

## Licencia

(véase el archivo LICENSE)
