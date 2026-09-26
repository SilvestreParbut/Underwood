# Changelog

Todos los cambios notables en Underwood se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).


## [2.1.0] — 2026-09-26

### Añadido
- **Interfaz bilingüe**: español e inglés.
- **Menú Idioma / Language** en la barra superior para cambiar de idioma
  sin reiniciar el programa. La preferencia se guarda en
  `~/.config/underwood/language` y se respeta en los siguientes arranques.
- Manual y "Acerca de" como archivos de texto externos, traducibles sin
  tocar el código.
- Nuevo ícono para la versión 2.1.
- Guardado automático del documento al cambiar de idioma, para no perder
  cambios sin guardar.

### Cambiado
- El paquete `.deb` ahora aparece en la categoría **Oficina** del menú de
  aplicaciones, en lugar de Accesorios.
- Descripción del paquete `.deb` bilingüe (inglés y español), para que
  cualquier usuario pueda identificar el programa al instalarlo.
- El arranque respeta este orden de prioridad para decidir el idioma:
  1. Archivo `~/.config/underwood/language`
  2. Variable de entorno `UNDERWOOD_LANG`
  3. Variable de entorno `LANG`
  4. Español por defecto

### Corregido
- La selección de texto con `Ctrl+A` era lenta en documentos grandes.
  Ahora el cálculo de la selección es de orden O(1) por carácter
  dibujado, en lugar de O(N) como antes.
- El arrastre con el ratón durante la selección se retrasaba en
  documentos largos cuando había muchos eventos pendientes.


## [2.0.0] — 2026-09-25

### Añadido
- **Barra de menús superior** con soporte de ratón: Archivo, Edición,
  Formato, Alineación, Insertar, Ayuda y Salir.
- **Menús desplegables** con atajos de teclado visibles.
- **Alineación de párrafos**: izquierda, centrada, derecha y justificada.
  Conserva la alineación al pasar entre sub-líneas y exporta a RTF con
  las directivas estándar `\ql`, `\qc`, `\qr`, `\qj`.
- **Salto de página** (`Ctrl+K`) que se guarda como `\page` en RTF y
  respeta LibreOffice al exportar a PDF.
- **Explorador de archivos** interno (`Ctrl+O`) dentro de la terminal.
- **Exportación asíncrona a PDF** con indicador de progreso (spinner
  braille). La interfaz sigue respondiendo mientras se genera el PDF.
- **Barra de estado inferior** con contador de palabras, formato activo
  y mensajes temporales.
- **Manual interno** (`Ctrl+G`) y **Acerca de** (`Ctrl+H`).
- **Selección con ratón** y scroll con rueda / trackpad.
- **Deshacer** (`Ctrl+Z`).
- **Seleccionar todo** (`Ctrl+A`).
- **Doble clic** en archivos `.rtf` desde el explorador del sistema los
  abre directamente en Underwood (asociación MIME).
- Paquete `.deb` con ícono propio, lanzador de escritorio y manual.

### Cambiado
- El renderizado de la selección se optimiza con pre-cálculo de offsets
  por línea, para acelerar el dibujado.
- El uso de CPU se reduce drásticamente al detener el reporte de
  movimiento del ratón cuando no hay interacción (modo `1002` en lugar
  de `1003` de los códigos de reporte del terminal).
- El ancho de pantalla se centra en 80 columnas para mejor legibilidad
  en pantallas panorámicas.

### Corregido
- Los caracteres hispanos (`ñ`, `á`, `¿`, `¡`, etc.) ya no se duplican
  al leer archivos RTF generados por LibreOffice. Se maneja correctamente
  la secuencia `\uN` seguida de su carácter de respaldo.
- Los cambios de formato (negrita, cursiva, subrayado) dentro de grupos
  RTF `{...}` ahora se revierten al cerrar el grupo, como indica el
  estándar.


## [1.0.0] — 2026-09-25

### Añadido
- Primera versión pública.
- Editor de texto enriquecido para la terminal.
- Soporte para **negrita**, **cursiva** y **subrayado**.
- **Búsqueda** (`Ctrl+F`) con contador de coincidencias y navegación
  con `Enter`.
- **Reemplazo** (`Ctrl+R`) de todas las coincidencias a la vez.
- **Cortar, copiar y pegar** con integración al portapapeles del sistema
  (`xclip` o `xsel`).
- **Guardado en formato .rtf** (Rich Text Format), compatible con
  LibreOffice Writer, Microsoft Word y otros procesadores.
- **Exportación a PDF** (requiere LibreOffice instalado, nativo o vía
  Flatpak).
- Interfaz a color, con formato visible en tiempo real.
- Paquete `.deb` instalable en Debian, Ubuntu y Linux Mint.

### Notas
- Esta versión es monolingüe (español).


[2.1.0]: https://github.com/tu_usuario/underwood/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/tu_usuario/underwood/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/tu_usuario/underwood/releases/tag/v1.0.0
