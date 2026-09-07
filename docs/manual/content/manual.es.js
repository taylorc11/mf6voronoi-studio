/* mf6Voronoi Studio 3.0.0 — Manual de Usuario (español).
 *
 * Traducción de manual.en.js; mantener ambos archivos en paralelo.
 *
 * Criterio de traducción: la aplicación NO está traducida, así que los
 * nombres de menús, botones, paneles y opciones se citan en inglés,
 * exactamente como aparecen en pantalla. Todo lo demás va en español.
 */
'use strict';

module.exports = {
  meta: {
    appName: 'mf6Voronoi Studio',
    docTitle: 'Manual de Usuario',
    versionLine: 'Versión 3.0.0',
    tagline: 'Cree, edite, refine y exporte mallas Voronoi DISV para MODFLOW 6',
    headerText: 'mf6Voronoi Studio 3.0.0 — Manual de Usuario',
    description: 'Manual de usuario de mf6Voronoi Studio 3.0.0',
    contentsTitle: 'Contenido',
    figureWord: 'Figura',
    pageWord: 'Página',
    coverImage: '17_mesh_generated',
    coverNotes: [
      'Todas las capturas y todas las cifras de este manual proceden de una ejecución real de',
      'mf6Voronoi Studio 3.0.0 sobre el conjunto de datos Example que acompaña a la aplicación.',
    ],
    credits: ['mf6Voronoi — Saul Montoya', 'Desarrollo de la interfaz — An Ho Taylor'],
    motto: 'Viva el Software Libre',
  },

  body: H => [
    ...H.cover(),
    ...H.contents(),

    /* ============================================== 1. Introducción == */
    H.h1('1. Introducción'),

    H.note('Sobre el idioma y los números.',
      'La aplicación está en inglés y no se traduce. Por eso los nombres de '
      + 'menús, botones y opciones aparecen aquí en inglés, tal como los verá '
      + 'en pantalla (por ejemplo File → Import limit polygon…). Además, la '
      + 'interfaz muestra las cifras en formato anglosajón (1,134 celdas; '
      + '44,293.75 m²), mientras que en este documento se usa la convención '
      + 'española (1134 celdas; 44.293,75 m²). Son los mismos valores.'),
    H.spacer(),

    H.h2('1.1  Qué hace mf6Voronoi Studio'),
    H.p('mf6Voronoi Studio es una aplicación de escritorio para Windows que '
      + 'construye mallas Voronoi no estructuradas para modelos de agua '
      + 'subterránea. Usted le proporciona un límite del modelo y un conjunto '
      + 'de elementos que la malla debe seguir de cerca —pozos, drenes, ríos, '
      + 'la huella de un emplazamiento, una barrera— y la aplicación genera una '
      + 'teselación de Voronoi fina cerca de esos elementos y progresivamente '
      + 'más gruesa a medida que se aleja de ellos.'),
    H.p('Es una interfaz gráfica para el paquete de Python mf6Voronoi, de '
      + 'Hatari Labs. Todo lo que el paquete hace por línea de comandos puede '
      + 'hacerse aquí con el ratón, y además puede revisar el resultado sobre '
      + 'un mapa antes de darlo por bueno.'),
    H.table(
      ['Lo que necesita', 'Cómo lo resuelve la aplicación'],
      [
        ['Crear, editar y exportar una malla Voronoi DISV',
          'Genera con mf6Voronoi; edita las capas en vivo; exporta shapefile, DISV JSON o un modelo para ModelMuse'],
        ['Manejar muchas capas de refinamiento',
          'Capas ilimitadas, cada una con su tamaño de celda objetivo, su visibilidad y su color'],
        ['Importar datos SIG',
          'Un polígono de límite más shapefiles de puntos, líneas y polígonos de refinamiento'],
        ['Importar una imagen de fondo',
          'GeoTIFF, o PNG/JPG con archivo de georreferenciación, o una extensión escrita a mano'],
        ['Refinar con puntos, líneas y polígonos',
          'Impórtelos, o dibújelos interactivamente sobre el mapa'],
        ['Controlar el refinamiento progresivo',
          'Tamaño de celda grueso, multiplicador de crecimiento, solape de refinamientos y corrección de aristas cortas'],
        ['Excluir zonas de la malla',
          'Polígonos de vacío: un lago o una zona excluida donde no se generan celdas'],
        ['Comprobar la calidad antes de modelar',
          'Un informe de conteo de celdas y calidad, exportable a CSV o JSON'],
        ['Llevar la malla a MODFLOW 6',
          'Una simulación MODFLOW 6 DISV completa, escrita con FloPy, que ModelMuse puede importar'],
        ['Guardar y retomar el trabajo',
          'Toda la sesión, malla incluida, en un único archivo .mf6vor'],
      ],
      [3200, 6880]),
    H.spacer(),

    H.h2('1.2  Cómo se construye la malla'),
    H.p('Tres cosas determinan el resultado. Entenderlas es casi todo lo que '
      + 'hace falta para usar bien la aplicación.'),
    H.bulletR([['El límite del modelo. ', 'b'],
      ['Un único polígono que delimita la malla. Exactamente un polígono de una '
       + 'sola parte: sin geometrías multiparte y sin huecos (para los huecos '
       + 'están los polígonos de vacío).']]),
    H.bulletR([['Las capas de refinamiento. ', 'b'],
      ['Puntos, líneas o polígonos, cada capa con su tamaño de celda objetivo. '
       + 'Cerca de los elementos de una capa, las celdas se generan '
       + 'aproximadamente con ese tamaño.']]),
    H.bulletR([['El tamaño de celda grueso y el multiplicador. ', 'b'],
      ['Lejos de todo elemento de refinamiento, las celdas crecen hasta el '
       + 'tamaño grueso (máximo). El multiplicador fija la rapidez de ese '
       + 'crecimiento: 1,3 significa que cada anillo sucesivo de celdas es un '
       + '30 % mayor que el anterior. Un multiplicador pequeño da una malla más '
       + 'suave y con más celdas; uno grande, una malla menor y con saltos más '
       + 'bruscos.']]),
    H.spacer(80),
    H.p('La aplicación siembra puntos según esas reglas, construye la teselación '
      + 'de Voronoi, la recorta contra el límite del modelo y le entrega las celdas.'),

    H.h2('1.3  Novedades de la versión 3.0.0'),
    H.p('La versión 3.0.0 añade una segunda forma de conseguir una imagen de '
      + 'fondo: además de importar un archivo, ahora puede desplazarse y '
      + 'hacer zoom sobre un mapa satelital en línea, elegir el área que '
      + 'necesita, y añadirla directamente como fondo — o exportarla como un '
      + 'GeoTIFF georreferenciado para guardarla y volver a importarla más '
      + 'tarde.'),
    H.p('File → Add background image (file or online map)… abre ahora un '
      + 'diálogo con dos pestañas. "From file" es el flujo de importación '
      + 'anterior, sin cambios. "Online satellite map" es nuevo: elija un '
      + 'proveedor de imágenes gratuito (Esri World Imagery o Sentinel-2 '
      + 'Cloudless), busque un lugar o ajuste la vista a la extensión de su '
      + 'proyecto, opcionalmente arrastre para marcar el área exacta que '
      + 'necesita, y pulse "Add to project as background…" o "Export '
      + 'GeoTIFF…". La imagen se descarga, se reproyecta al sistema de '
      + 'coordenadas del proyecto (o a una zona UTM detectada automáticamente '
      + 'si aún no hay ninguno definido), y se escribe como un GeoTIFF normal '
      + 'con el CRS incrustado — sin necesidad de world file.'),
    H.note('Imágenes gratuitas, uso personal / de evaluación.', 'Ambos '
      + 'proveedores son gratuitos y no requieren clave de API, pero revise '
      + 'sus condiciones de uso antes de emplear la imagen exportada con fines '
      + 'comerciales o de redistribuirla.'),
    H.spacer(),
    H.p('Versiones anteriores corrigieron un error de refinamiento que '
      + 'afectaba a un caso muy habitual: si un elemento de refinamiento '
      + 'discurría más cerca del borde del modelo que su propio tamaño de '
      + 'celda objetivo —por ejemplo, una línea de condición de contorno de '
      + 'carga general que sigue el borde del dominio—, mf6Voronoi descartaba '
      + 'en silencio todos los puntos semilla de esa capa, sin ningún aviso '
      + '(2.0.5). El tutorial del capítulo 5 ejercita exactamente este caso: '
      + 'la capa modelGhb discurre junto al borde del modelo y se refina '
      + 'correctamente.'),
    H.ok('Comprobado.', 'En la ejecución del tutorial, el área de la malla '
      + 'recortada resultó ser de 44.293,75 m², idéntica al área del polígono '
      + 'de límite: el recorte no deja huecos ni solapes.'),
    H.spacer(),
    H.p('Las versiones anteriores de la línea 2.0 también añadieron: varias '
      + 'imágenes de fondo (2.0.3), una notificación de malla terminada y un '
      + 'aviso emergente dentro de la aplicación (2.0.3 y 2.0.4), una '
      + 'herramienta de medición de distancias, "Save project as…" y el aviso '
      + 'de cambios sin guardar (2.0.2), los polígonos de vacío (2.0.1) y un '
      + 'lienzo de mapa reconstruido con aceleración por hardware e interfaz '
      + 'oscura (2.0.0).'),

    H.h2('1.4  Requisitos y limitaciones'),
    H.bullet('Windows. La aplicación se distribuye como instalador, como ZIP portable o como código fuente de Python.'),
    H.bulletR([['Todas las entradas deben compartir un mismo sistema de coordenadas proyectado, en metros o en pies. ', 'b'],
      ['Los sistemas geográficos (latitud/longitud) se rechazan, porque los '
       + 'tamaños de celda se expresan como una distancia.']]),
    H.bullet('El límite del modelo debe ser exactamente un polígono de una sola parte.'),
    H.bullet('Los elementos de refinamiento multiparte se descomponen en partes simples al importarlos.'),
    H.bullet('Una celda DISV no puede tener un hueco, por lo que los polígonos de vacío eliminan o recortan celdas en lugar de perforarlas.'),
    H.pageBreak(),

    /* ========================================= 2. Instalación == */
    H.h1('2. Instalación y primer arranque'),

    H.h2('2.1  Instalación'),
    H.table(
      ['Opción', 'Qué obtiene', 'Recomendada para'],
      [
        [[['mf6VoronoiStudio-3.0.0-Setup.exe', 'c']],
          'Instala en Archivos de programa, con accesos directos y desinstalador',
          'Uso habitual en su propio equipo'],
        ['ZIP portable', 'Una carpeta autocontenida: descomprimir y ejecutar, sin instalar nada',
          'Memorias USB y equipos con restricciones'],
        ['Código fuente de Python', 'Ejecutar directamente desde el repositorio con su propio Python',
          'Desarrollo y personalización'],
      ],
      [3000, 4200, 2880]),
    H.spacer(120),
    H.rp([['Para ejecutar desde el código fuente necesita Python 3.10–3.12 '
      + '(64 bits). Instale las dependencias con ', ''],
      ['pip install -r requirements.txt', 'c'],
      [' y arranque la aplicación con ', ''],
      ['python mf6voronoi_gui.py', 'c'], ['.', '']]),
    H.note('Consejo.', 'Si al escribir "python" Windows le ofrece la Microsoft '
      + 'Store, es que Python no está realmente instalado. Instálelo desde '
      + 'python.org, marque "Add python.exe to PATH" y, si hace falta, desactive '
      + 'los alias de la Store en Configuración → Aplicaciones → Configuración '
      + 'avanzada de aplicaciones → Alias de ejecución de aplicaciones. En '
      + 'Windows puede hacer doble clic en CHECK_PYTHON.bat para comprobarlo y '
      + 'después en build_windows.bat.'),
    H.spacer(),

    H.h2('2.2  La ventana principal'),
    H.p('La aplicación arranca con un proyecto vacío: no hay nada cargado, no '
      + 'hay sistema de coordenadas definido y el mapa está en blanco.'),
    ...H.figure('01_main_empty', H.PX,
      'mf6Voronoi Studio 3.0.0 recién arrancado, con un proyecto vacío.'),
    H.p('La ventana tiene cuatro zonas:'),
    H.bulletR([['La barra de menús ', 'b'], ['— File, Draw, View y Help (capítulo 3).']]),
    H.bulletR([['La barra de herramientas ', 'b'],
      ['— acceso directo a los modos de dibujo, a la generación de la malla y al zoom.']]),
    H.bulletR([['El lienzo del mapa ', 'b'],
      ['— a la izquierda, ocupa la mayor parte de la ventana. Aquí se desplaza, '
       + 'hace zoom, dibuja y selecciona.']]),
    H.bulletR([['El panel lateral ', 'b'],
      ['— a la derecha, una columna desplazable de paneles ordenados de arriba '
       + 'abajo según el orden habitual de trabajo: sistema de coordenadas, '
       + 'imágenes de fondo, capas de refinamiento, polígonos de vacío, '
       + 'opciones de refinamiento, malla, informe de calidad y registro '
       + '(capítulo 4).']]),
    H.spacer(80),
    H.p('El panel lateral es más alto que la ventana, así que hay que '
      + 'desplazarlo para llegar a los paneles inferiores.'),
    ...H.figure('29_main_sidebar_scrolled', H.PX,
      'La misma ventana con el panel lateral desplazado hasta las opciones de '
      + 'refinamiento y los paneles Mesh, informe de calidad y Log.'),
    H.pageBreak(),

    /* ================================================== 3. Menús == */
    H.h1('3. Referencia de menús, barra de herramientas y controles'),

    H.h2('3.1  Menú File'),
    ...H.figure('11_menu_file', H.PX, 'El menú File.'),
    H.table(
      ['Comando', 'Atajo', 'Qué hace'],
      [
        ['New project', 'Ctrl+N', 'Vacía todo y empieza de cero. Antes pregunta si hay cambios sin guardar.'],
        ['Open project…', 'Ctrl+O', 'Abre un proyecto .mf6vor guardado, con su malla incluida.'],
        ['Save project', 'Ctrl+S', 'Guarda en el archivo actual. Solo pregunta la ubicación la primera vez.'],
        ['Save project as…', 'Ctrl+Shift+S', 'Guarda en un archivo nuevo y lo convierte en el archivo actual.'],
        ['Import limit polygon…', '', 'Carga el límite del modelo desde un shapefile de polígonos. Adopta el CRS del archivo .prj si aún no hay ninguno definido.'],
        ['Import refinement shapefile…', '', 'Carga un shapefile de puntos, líneas o polígonos como capa de refinamiento; pide un nombre y un tamaño de celda objetivo.'],
        ['Add background image (file or online map)…', '', 'Abre un diálogo con dos pestañas: importación desde archivo local, o mapa satelital en línea interactivo. Se puede repetir: admite varias.'],
        ['Remove background image', '', 'Elimina la imagen de fondo seleccionada.'],
        ['Import void polygon shapefile…', '', 'Carga uno o varios polígonos dentro de los cuales no se generarán celdas.'],
        ['Export mesh shapefile…', '', 'Escribe las celdas generadas como shapefile de polígonos ESRI, con su .prj.'],
        ['Export DISV properties (JSON)…', '', 'Escribe los arreglos DISV —vertices, cell2d, ncpl, nvert— en formato JSON.'],
        ['Export quality report…', '', 'Escribe el informe actual como CSV o JSON.'],
        ['Export ModelMuse MODFLOW 6 model…', '', 'Escribe una simulación MODFLOW 6 DISV completa, lista para importar en ModelMuse.'],
        ['Quit', '', 'Cierra la aplicación, preguntando si hay cambios sin guardar.'],
      ],
      [3100, 1500, 5480]),
    H.pageBreak(),

    H.h2('3.2  Menú Draw'),
    H.p('El menú Draw determina qué hace un clic sobre el mapa. Solo hay un '
      + 'modo activo a la vez, y su botón de la barra de herramientas permanece '
      + 'pulsado mientras lo está.'),
    ...H.figure('12_menu_draw', H.PX, 'El menú Draw.'),
    H.table(
      ['Comando', 'Qué hace'],
      [
        ['Navigate (pan/zoom)', 'El modo por defecto. Arrastrar desplaza el mapa; hacer clic selecciona elementos.'],
        ['Draw limit polygon', 'Digitaliza el límite del modelo directamente sobre el mapa, en lugar de importarlo.'],
        ['New point refinement layer…', 'Pide nombre y tamaño de celda; después, cada clic coloca un punto de refinamiento.'],
        ['New polyline refinement layer…', 'Pide nombre y tamaño de celda; después digitaliza una o varias polilíneas.'],
        ['New polygon refinement layer…', 'Pide nombre y tamaño de celda; después digitaliza uno o varios polígonos.'],
        ['New void polygon…', 'Digitaliza un polígono dentro del cual no se generarán celdas.'],
        ['Finish current layer', 'Confirma los elementos dibujados hasta el momento y vuelve al modo Navigate.'],
        ['Cancel current layer', 'Descarta todo lo dibujado en la sesión actual y vuelve al modo Navigate.'],
      ],
      [3400, 6680]),
    H.spacer(140),

    H.h2('3.3  Menú View'),
    ...H.figure('13_menu_view', H.PX, 'El menú View.'),
    H.table(
      ['Comando', 'Qué hace'],
      [
        ['Zoom to data', 'Ajusta la vista a todo lo cargado: límite, capas, malla e imágenes de fondo.'],
        ['Zoom in / Zoom out', 'Cambia el nivel de zoom por pasos. La rueda del ratón hace lo mismo de forma continua.'],
        ['Measure distance', 'Haga clic en un punto inicial y otro final para leer la distancia en la unidad de longitud del proyecto. Otro clic inicia una medición nueva; Esc cancela la que esté en curso.'],
      ],
      [3400, 6680]),
    H.spacer(140),

    H.h2('3.4  Menú Help'),
    H.p('El menú Help contiene un único comando, About, que informa de la '
      + 'versión exacta que está ejecutando: útil para comprobar si dispone de '
      + 'la pestaña de imágenes en línea de la versión 3.0.0 o de la '
      + 'corrección de refinamiento en el borde de la versión 2.0.5.'),
    ...H.figure('27_dialog_about', 330, 'Help → About confirma la versión en ejecución.'),
    H.pageBreak(),

    H.h2('3.5  Barra de herramientas'),
    ...H.figure('15_toolbar', H.PX,
      'La barra de herramientas. Los siete primeros botones son modos y '
      + 'permanecen pulsados mientras están activos.'),
    H.table(
      ['Nº', 'Botón', 'Comando de menú equivalente'],
      [
        ['1', 'Navigate (flecha)', 'Draw → Navigate (pan/zoom)'],
        ['2', 'Limit', 'Draw → Draw limit polygon'],
        ['3', '+Points', 'Draw → New point refinement layer…'],
        ['4', '+Lines', 'Draw → New polyline refinement layer…'],
        ['5', '+Polygons', 'Draw → New polygon refinement layer…'],
        ['6', '+Void', 'Draw → New void polygon…'],
        ['7', 'Measure', 'View → Measure distance'],
        ['8', 'Finish layer (visto bueno)', 'Draw → Finish current layer'],
        ['9', 'Cancel layer (papelera)', 'Draw → Cancel current layer'],
        ['10', 'Generate mesh (engranaje)', 'El botón "Generate Voronoi mesh" del panel Mesh'],
        ['11', 'Zoom in', 'View → Zoom in'],
        ['12', 'Zoom out', 'View → Zoom out'],
        ['13', 'Fit to data', 'View → Zoom to data'],
      ],
      [700, 3300, 6080]),
    H.spacer(140),

    H.h2('3.6  Ratón y teclado sobre el mapa'),
    H.table(
      ['Acción', 'En modo Navigate', 'Mientras dibuja'],
      [
        ['Clic izquierdo', 'Selecciona un elemento (una imagen de fondo, un vacío)', 'Añade un vértice; en modo punto, coloca un punto de inmediato'],
        ['Arrastrar con el botón izquierdo', 'Desplaza el mapa', '—'],
        ['Arrastrar con el botón central', 'Desplaza el mapa', 'Desplaza el mapa (funciona en todos los modos)'],
        ['Doble clic', '—', 'Añade el último vértice y termina la geometría actual'],
        ['Rueda del ratón', 'Acerca y aleja la vista', 'Acerca y aleja la vista'],
        [[['Enter', 'c']], '—', 'Termina la geometría actual'],
        [[['Esc', 'c']], 'Deselecciona todo', 'Cancela la geometría o la medición en curso'],
        [[['Supr', 'c'], [' / ', ''], ['Retroceso', 'c']], 'Elimina la imagen de fondo o el polígono de vacío seleccionado', '—'],
      ],
      [1900, 3900, 4280]),
    H.spacer(140),

    H.h2('3.7  Atajos de teclado'),
    H.table(
      ['Atajo', 'Comando'],
      [
        [[['Ctrl+N', 'c']], 'New project (nuevo proyecto)'],
        [[['Ctrl+O', 'c']], 'Open project… (abrir proyecto)'],
        [[['Ctrl+S', 'c']], 'Save project (guardar proyecto)'],
        [[['Ctrl+Shift+S', 'c']], 'Save project as… (guardar como)'],
        [[['Enter', 'c']], 'Termina la geometría que está dibujando'],
        [[['Esc', 'c']], 'Cancela la geometría o medición en curso; si no hay ninguna, deselecciona'],
        [[['Supr', 'c']], 'Elimina la imagen de fondo o el polígono de vacío seleccionado'],
      ],
      [2400, 7680]),
    H.pageBreak(),

    /* ================================================= 4. Paneles == */
    H.h1('4. Los paneles laterales'),

    H.h2('4.1  Sistema de coordenadas (CRS)'),
    H.p('Es lo primero que hay que definir y lo que bloquea todo lo demás. Los '
      + 'tamaños de celda son distancias, así que el proyecto necesita un '
      + 'sistema de coordenadas proyectado cuya unidad sea el metro o el pie. '
      + 'Mientras no haya un CRS definido, el panel muestra "No CRS set" y se '
      + 'rechaza la importación de capas de refinamiento.'),
    ...H.figure('02_panel_crs_empty', 430, 'El panel CRS antes de definir el sistema de coordenadas.'),
    ...H.figure('04_panel_crs_set', 430,
      'Tras definir EPSG:32631. El panel nombra el sistema y confirma su unidad de longitud.'),
    H.note('Importante.', 'Todos los shapefiles que importe deben usar '
      + 'exactamente este sistema de coordenadas. La aplicación lee el CRS '
      + 'automáticamente del archivo .prj del shapefile y rechaza cualquier '
      + 'archivo cuyo CRS difiera del del proyecto. Reproyecte antes en su SIG '
      + 'los datos que no coincidan.'),
    H.spacer(),

    H.h2('4.2  Imágenes de fondo'),
    H.p('Imágenes georreferenciadas opcionales que se dibujan bajo el mapa: una '
      + 'ortofoto, un plano escaneado, una figura publicada, o un mapa base '
      + 'satelital descargado en línea. Añada todas las que necesite; cada una '
      + 'ocupa una fila con su casilla de visibilidad. Seleccione una imagen '
      + 'haciendo clic sobre ella en el mapa y elimínela con el botón Remove '
      + 'del panel, con la tecla Supr o con File → Remove background image. '
      + 'Pulse Esc o haga clic en una zona vacía para deseleccionar.'),
    H.p('El botón Add… del panel (y File → Add background image (file or '
      + 'online map)…) abre un diálogo con dos pestañas:'),
    H.bulletR([['From file. ', 'b'],
      ['Un GeoTIFF lleva su propia extensión. Un PNG o un JPG normal necesita '
       + 'o bien un archivo de georreferenciación (world file) junto a él, o '
       + 'bien una extensión que usted escriba a mano.']]),
    H.bulletR([['Online satellite map. ', 'b'],
      ['Desplácese y haga zoom sobre un proveedor de imágenes gratuito, '
       + 'busque un lugar, o ajuste la vista a la extensión actual del '
       + 'proyecto; después añádala al proyecto o expórtela como GeoTIFF. '
       + 'Vea la sección 6.3 para el flujo completo.']]),

    H.h2('4.3  Capas de refinamiento'),
    H.p('El corazón de la herramienta. Cada fila muestra una casilla de '
      + 'visibilidad, el nombre de la capa, su tipo de geometría y su tamaño de '
      + 'celda objetivo, con el mismo color que en el mapa.'),
    ...H.figure('08_panel_layers', 430,
      'El panel de capas de refinamiento con las cinco capas del tutorial del capítulo 5.'),
    H.bulletR([['Edit size… ', 'b'], ['cambia el tamaño de celda objetivo (y el nombre) de una capa.']]),
    H.bulletR([['Delete ', 'b'], ['elimina la capa seleccionada.']]),
    H.bulletR([['Layer top/botm rasters… ', 'b'],
      ['asocia rásteres de elevación a la capa, que después rellenan '
       + 'automáticamente el diálogo de exportación a ModelMuse.']]),
    H.spacer(80),
    H.p('Desmarcar una capa solo la oculta en el mapa: sigue participando en el '
      + 'mallado. Si quiere excluirla, elimínela.'),

    H.h2('4.4  Polígonos de vacío'),
    H.p('Polígonos situados dentro del límite del modelo donde no se generan '
      + 'celdas: un lago, la huella de un edificio, una zona fuera del '
      + 'acuífero. Puede dibujarlos o importarlos desde un shapefile.'),
    ...H.figure('09_panel_voids', 430,
      'El panel de polígonos de vacío (vacío en el proyecto del tutorial).'),
    H.p('mf6Voronoi no contempla de forma nativa el concepto de hueco, así que '
      + 'la aplicación siembra puntos a lo largo del contorno de cada vacío para '
      + 'obtener un borde limpio y después elimina o recorta las celdas que caen '
      + 'dentro. Nunca queda una celda con un hueco, porque el formato DISV no '
      + 'puede representarlo.'),

    H.h2('4.5  Opciones de refinamiento Voronoi'),
    ...H.figure('10_panel_options', 430,
      'Las opciones de refinamiento, con los valores usados en el tutorial.'),
    H.table(
      ['Opción', 'Significado', 'Recomendación'],
      [
        ['Coarse (max) cell size',
          'La celda mayor que producirá la malla, usada lejos de todo elemento de refinamiento.',
          'Empiece por 1/15 a 1/20 del lado menor de su modelo.'],
        ['Refinement multiplier',
          'Rapidez con la que crecen las celdas entre un elemento de refinamiento y el tamaño grueso. 1,3 equivale a un 30 % por anillo.',
          'Rango 1,0–10,0. Lo habitual es 1,2–1,5. Un valor menor suaviza la transición pero genera más celdas.'],
        ['Allow overlapping refinement',
          'Permite que las zonas de refinamiento de distintas capas se solapen en vez de competir entre sí.',
          'Déjelo activado salvo que tenga un motivo concreto para no hacerlo.'],
        ['Fix short edges below',
          'Tras la primera teselación, las celdas con alguna arista más corta que este valor se vuelven a sembrar y la malla se regenera. Con 0 se desactiva esta pasada.',
          'Una fracción pequeña de su tamaño de celda objetivo más fino. Vea la advertencia de la sección 5.7.'],
      ],
      [2500, 4200, 3380]),
    H.spacer(140),

    H.h2('4.6  Panel Mesh (malla)'),
    ...H.figure('18_panel_mesh', 430, 'El panel Mesh tras una ejecución correcta.'),
    H.p('"Generate Voronoi mesh" ejecuta el mallado en segundo plano, de modo '
      + 'que la ventana sigue respondiendo y el panel Log se va rellenando '
      + 'durante el proceso. La etiqueta inferior indica el número de celdas. '
      + '"Show generated mesh" oculta la malla sin borrarla, algo útil cuando '
      + 'quiere seguir editando capas de refinamiento sobre un mapa cargado.'),

    H.h2('4.7  Informe de conteo de celdas y calidad'),
    H.p('Se rellena automáticamente al terminar una malla y puede recalcularse '
      + 'en cualquier momento. "Save report…" lo guarda como CSV o JSON.'),
    ...H.figure('19_panel_report', 400, 'El informe de calidad de la malla del tutorial.'),
    H.table(
      ['Métrica', 'Qué le indica'],
      [
        ['Cells (ncpl)', 'Número de celdas por capa: el tamaño de su malla.'],
        ['Vertices (nvert)', 'Número de vértices únicos. Muestra 0 hasta que se calculan las propiedades DISV (vea la nota de la sección 5.7).'],
        ['Cell area min / max / mean / median', 'La dispersión de tamaños de celda. Compare el máximo con su tamaño grueso y el mínimo con su objetivo más fino.'],
        ['Total area', 'Debe coincidir con el área del polígono de límite. Si es menor, el recorte perdió celdas.'],
        ['Vertices per cell', 'Las celdas Voronoi típicas tienen de 5 a 7 lados. Un máximo alto indica transiciones de refinamiento demasiado bruscas.'],
        ['Shortest edge / Mean of min edges', 'La arista más corta de toda la malla y la media por celda. Las aristas muy cortas pueden endurecer la solución de MODFLOW.'],
        ['Short-edge threshold', 'El valor de "Fix short edges below": el patrón de medida de la fila siguiente.'],
        ['Cells with short edges', 'Cuántas celdas tienen alguna arista por debajo de ese umbral. Se muestra en rojo cuando no es cero.'],
      ],
      [3200, 6880]),
    H.spacer(140),

    H.h2('4.8  Panel Log (registro)'),
    H.p('Una transcripción continua de todo lo que informan la aplicación y el '
      + 'paquete mf6Voronoi: el avance de la nube de puntos, la pasada de '
      + 'corrección de aristas cortas, el recorte, los avisos y las trazas '
      + 'completas si algo falla. Es lo primero que hay que leer cuando una '
      + 'ejecución no hace lo que esperaba.'),
    ...H.figure('20_panel_log', 430, 'El panel Log al final de la ejecución del tutorial.'),
    H.pageBreak(),

    /* =============================================== 5. Tutorial == */
    H.h1('5. Tutorial: mallado del conjunto de datos Example'),
    H.p('Este capítulo recorre el flujo de trabajo completo usando la carpeta '
      + 'Example que acompaña a la aplicación. Todo lo que aquí se muestra '
      + 'procede de una ejecución real: las capturas, el número de celdas y las '
      + 'cifras del informe corresponden a la misma sesión.'),

    H.h2('5.0  Qué contiene la carpeta Example'),
    H.p('Un modelo de emplazamiento pequeño en WGS 84 / UTM zona 31N '
      + '(EPSG:32631), con el metro como unidad de longitud. El límite del '
      + 'modelo abarca unos 302 m de este a oeste por 291 m de norte a sur, y '
      + 'encierra 44.293,7 m².'),
    H.table(
      ['Archivo', 'Geometría', 'Elementos', 'Papel en este tutorial'],
      [
        [[['modelLimit.shp', 'c']], 'Polígono', '1', 'El límite del modelo'],
        [[['modelGhb.shp', 'c']], 'Línea', '2', 'Contorno de carga general junto al borde del modelo: capa de refinamiento'],
        [[['site.shp', 'c']], 'Polígono', '1', 'Huella del emplazamiento: capa de refinamiento'],
        [[['hfb.shp', 'c']], 'Línea', '1', 'Barrera de flujo horizontal: capa de refinamiento'],
        [[['drains.shp', 'c']], 'Línea', '2', 'Drenes: capa de refinamiento'],
        [[['pointWell.shp', 'c']], 'Punto', '2', 'Pozos de bombeo: capa de refinamiento'],
        [[['crossSection.shp', 'c']], 'Línea', '1', 'Traza de una sección (no se usa para refinar aquí)'],
        [[['rasterExtension.shp', 'c']], 'Polígono', '1', 'Extensión del MDT (no se usa para refinar)'],
        [[['modelTop.tif', 'c']], 'Ráster', '106×99', 'Cota superior del modelo, 0 m'],
        [[['bottomLy1–4.tif', 'c']], 'Ráster', '106×99', 'Bases de capa a −4, −7,5, −20 y −50 m'],
        [[['modelDem.tif', 'c']], 'Ráster', '121×119', 'MDT de la superficie del terreno, 1 m'],
      ],
      [2400, 1500, 1300, 4880]),
    H.spacer(120),
    H.ok('Nota.', 'modelGhb discurre justo a lo largo del borde del modelo, más '
      + 'cerca del borde que su propio tamaño de celda objetivo de 10 m. Antes '
      + 'de la versión 2.0.5 esta capa se habría ignorado en silencio. Se '
      + 'incluye aquí a propósito, para ejercitar la corrección.'),
    H.spacer(),

    H.h2('5.1  Paso 1 — Definir el sistema de coordenadas'),
    H.stepR([['Pulse ', ''], ['Set / change CRS…', 'b'], [' en el panel Coordinate system.', '']]),
    H.stepR([['Escriba ', ''], ['32631', 'c'],
      [': basta con el código EPSG, aunque también admite una cadena PROJ o WKT completa.', '']]),
    H.step('El diálogo valida a medida que escribe y nombra el sistema que ha resuelto, para que pueda confirmarlo antes de aceptar.'),
    H.stepR([['Pulse ', ''], ['OK', 'b'], ['.', '']]),
    ...H.figure('03_dialog_crs', 330, 'Definiendo el sistema de coordenadas del proyecto como EPSG:32631.'),
    H.p('El panel muestra entonces "WGS 84 / UTM zone 31N (EPSG:32631) — unit: '
      + 'meter". A partir de aquí, todos los tamaños de celda que escriba están '
      + 'en metros.'),
    ...H.figure('04_panel_crs_set', 430, 'El panel CRS una vez definido el sistema de coordenadas.'),
    H.note('Atajo.', 'Puede saltarse este paso: al importar primero el polígono '
      + 'de límite, la aplicación adopta automáticamente el CRS de su archivo '
      + '.prj. El tutorial lo define de forma explícita solo para mostrar el diálogo.'),
    H.spacer(),

    H.h2('5.2  Paso 2 — Importar el límite del modelo'),
    H.stepR([['Elija ', ''], ['File → Import limit polygon…', 'b'], ['.', '']]),
    H.stepR([['Seleccione ', ''], ['Example\\modelLimit.shp', 'c'], ['.', '']]),
    H.spacer(60),
    H.p('El límite aparece en color cian y el mapa se ajusta a él. El panel Log '
      + 'registra la importación y el CRS detectado.'),
    ...H.figure('05_limit_imported', H.PX, 'El límite del modelo cargado y ajustado a la ventana.'),
    H.note('Si el límite no se carga.', 'Debe ser exactamente un polígono de '
      + 'una sola parte. Una geometría multiparte, o un archivo con varios '
      + 'polígonos, se reducirá a su parte mayor: si no es lo que quiere, '
      + 'disuélvalo o recórtelo antes en su SIG.'),
    H.spacer(),

    H.h2('5.3  Paso 3 — Añadir las capas de refinamiento'),
    H.p('Repita esta secuencia para cada una de las cinco capas:'),
    H.stepR([['Elija ', ''], ['File → Import refinement shapefile…', 'b'], ['.', '']]),
    H.step('Seleccione el shapefile.'),
    H.step('Dé un nombre a la capa y su tamaño de celda objetivo, y pulse OK.'),
    ...H.figure('06_dialog_refinement_size', 320,
      'El diálogo de refinamiento. La unidad del tamaño de celda sigue al CRS '
      + 'del proyecto: metros en este caso.'),
    H.p('Importe las cinco capas con estos tamaños. Van descendiendo desde el '
      + 'contorno hasta los pozos, de modo que las celdas se hacen más gruesas '
      + 'de forma suave hacia el exterior:'),
    H.table(
      ['Orden', 'Shapefile', 'Nombre de capa', 'Geometría', 'Tamaño de celda objetivo'],
      [
        ['1', [['modelGhb.shp', 'c']], 'modelGhb', 'Línea (2 elementos)', '10 m'],
        ['2', [['site.shp', 'c']], 'site', 'Polígono (1 elemento)', '4 m'],
        ['3', [['hfb.shp', 'c']], 'hfb', 'Línea (1 elemento)', '3 m'],
        ['4', [['drains.shp', 'c']], 'drains', 'Línea (2 elementos)', '2 m'],
        ['5', [['pointWell.shp', 'c']], 'pointWell', 'Punto (2 elementos)', '1 m'],
      ],
      [900, 2400, 2000, 2700, 2080]),
    H.spacer(120),
    H.p('Cada capa se dibuja con su propio color, y el panel las lista en el '
      + 'orden en que se importaron.'),
    ...H.figure('07_layers_loaded', H.PX,
      'Las cinco capas de refinamiento cargadas. El contorno de carga general, '
      + 'en rojo, sigue el borde del modelo; el emplazamiento, la barrera, los '
      + 'drenes y los pozos se agrupan en el centro.'),
    ...H.figure('08_panel_layers', 430, 'El panel de capas tras importar las cinco.'),
    H.spacer(),

    H.h2('5.4  Paso 4 — Ajustar las opciones de refinamiento'),
    H.p('Desplace el panel lateral hasta "Voronoi refinement options" e '
      + 'introduzca lo siguiente:'),
    H.table(
      ['Opción', 'Valor', 'Por qué'],
      [
        ['Coarse (max) cell size', '20 m', 'Alrededor de 1/15 del lado corto del modelo (291 m): grueso en las esquinas vacías y aun así suficiente para resolver el dominio.'],
        ['Refinement multiplier', '1,3', 'Un crecimiento suave del 30 % por anillo, de modo que el salto de 1 m en los pozos a 20 m en los bordes resulte gradual.'],
        ['Allow overlapping refinement', 'Activado', 'El emplazamiento, la barrera, los drenes y los pozos se superponen entre sí.'],
        ['Fix short edges below', '0,2 m', 'Una quinta parte del objetivo más fino (1 m). Lea la advertencia de la sección 5.7 antes de cambiarlo.'],
      ],
      [2900, 1300, 5880]),
    H.spacer(120),
    ...H.figure('10_panel_options', 430, 'Las opciones de refinamiento de este tutorial.'),
    H.spacer(),

    H.h2('5.5  Paso 5 — Generar la malla'),
    H.stepR([['Pulse ', ''], ['⚙  Generate Voronoi mesh', 'b'],
      [' en el panel Mesh, o el botón del engranaje de la barra de herramientas.', '']]),
    H.step('Dé un nombre a la malla: será el prefijo de los archivos exportados. El valor por defecto es voronoiModel.'),
    ...H.figure('16_dialog_mesh_name', 260, 'Asignando nombre a la malla antes de generarla.'),
    H.p('El mallado se ejecuta en segundo plano y el panel Log se va '
      + 'rellenando. Este ejemplo terminó en unos tres segundos. Al acabar '
      + 'aparece un aviso emergente dentro de la aplicación y una notificación '
      + 'de Windows, de modo que puede dejar la ventana en segundo plano.'),
    ...H.figure('23_popup_mesh_done', 380,
      'El aviso de finalización, que repite las cifras principales de calidad.'),
    ...H.figure('17_mesh_generated', H.PX,
      'La malla terminada: 1134 celdas, finas en el centro y gruesas hacia las esquinas.'),
    H.spacer(),

    H.h2('5.6  Paso 6 — Inspeccionar la malla'),
    H.p('Acérquese al centro del modelo para ver el refinamiento en acción. Use '
      + 'la rueda del ratón, los botones de zoom de la barra de herramientas o '
      + 'View → Zoom to data para volver a la vista general.'),
    ...H.figure('22_canvas_zoom_site', 600,
      'Refinamiento progresivo alrededor del emplazamiento: celdas de 20 m '
      + 'arriba, que se van cerrando a través de la huella del emplazamiento '
      + 'hasta 1 m en los dos pozos (magenta). La barrera está en azul y los '
      + 'drenes en naranja.'),
    H.p('Esta es la comprobación que conviene hacer siempre: las celdas deben '
      + 'cerrarse de forma gradual hacia cada elemento, sin saltos bruscos de '
      + 'grueso a fino. Un salto brusco significa que el multiplicador es '
      + 'demasiado alto para el rango de tamaños que ha pedido.'),
    H.spacer(),

    H.h2('5.7  Paso 7 — Leer el informe de calidad'),
    H.p('El informe se rellena automáticamente. Estas son las cifras reales de '
      + 'esta ejecución:'),
    H.table(
      ['Métrica', 'Valor', 'Cómo interpretarlo'],
      [
        ['Cells (ncpl)', '1134', 'Un tamaño cómodo para un modelo de emplazamiento.'],
        ['Vertices (nvert)', '0 → 2527', 'Muestra 0 hasta que se calculan las propiedades DISV; tras exportar DISV o el modelo para ModelMuse informa de 2527.'],
        ['Cell area min', '0,00 m²', 'Astillas que quedan donde la teselación se recortó contra el borde. Solo tres celdas bajan de 0,01 m², y las tres están en el contorno.'],
        ['Cell area max', '400,00 m²', 'Exactamente el tamaño grueso de 20 m al cuadrado: se alcanzó el valor configurado.'],
        ['Cell area mean / median', '39,06 / 3,60 m²', 'La diferencia entre ambas es el refinamiento haciendo su trabajo: la mayoría de celdas son pequeñas y unas pocas, gruesas.'],
        ['Total area', '44.293,75 m²', 'Idéntica al área del polígono de límite: el recorte es exacto.'],
        ['Vertices per cell', '3 / 29 / 6,10', 'Una media próxima a seis es saludable en una malla Voronoi.'],
        ['Shortest edge', '0,0066 m', 'La arista más corta de toda la malla.'],
        ['Mean of min edges', '1,2749 m', 'Las celdas típicas están lejos de ser degeneradas.'],
        ['Cells with short edges', '220', 'Celdas con alguna arista por debajo del umbral de 0,2 m. Vea la advertencia siguiente.'],
      ],
      [2500, 1900, 5680]),
    H.spacer(140),
    H.note('Cómo leer correctamente "Cells with short edges".',
      'Este recuento es relativo al umbral que usted fija, así que es fácil '
      + 'malinterpretarlo. Sobre esta misma malla, con un umbral de 0,5 m se '
      + 'señala el 60 % de las celdas; con 0,2 m, el 19 %. Es aritmética, no un '
      + 'defecto: una teselación de Voronoi con celdas objetivo de 1 m tiene, '
      + 'por naturaleza, muchas aristas de menos de medio metro. Fije el umbral '
      + 'en una fracción pequeña de su tamaño objetivo más fino y trate la cifra '
      + 'como una tendencia que vigilar entre ejecuciones, no como un aprobado o '
      + 'suspenso absoluto.'),
    H.spacer(120),
    H.p('El panel Log deja constancia explícita del recorte contra el borde:'),
    ...H.figure('20_panel_log', 430,
      'El registro confirma el recorte y el número final de celdas. "20 '
      + 'sliver/empty cell(s) removed" es la solución de la versión 2.0.5 '
      + 'recogiendo sus propias astillas.'),
    H.rp([['Guarde el informe con ', ''], ['Save report…', 'b'], [' o con ', ''],
      ['File → Export quality report…', 'b'],
      [', en formato CSV o JSON. Conviene conservarlo junto al modelo como '
       + 'constancia de la malla construida.', '']]),
    H.spacer(),

    H.h2('5.8  Paso 8 — Exportar la malla y las propiedades DISV'),
    H.table(
      ['Comando', 'Produce', 'Sirve para'],
      [
        ['File → Export mesh shapefile…',
          [['voronoiModel_voronoi.shp', 'c'], [' más .shx, .dbf, .prj y .cpg', '']],
          'Ver o posprocesar la malla en QGIS o ArcGIS'],
        ['File → Export DISV properties (JSON)…',
          [['voronoiModel_disv.json', 'c']],
          'Programar con FloPy, o alimentar otra herramienta con los arreglos DISV en bruto'],
        ['File → Export quality report…',
          [['voronoiModel_report.csv', 'c'], [' o .json', '']],
          'Documentar la malla'],
      ],
      [3300, 3300, 3480]),
    H.spacer(120),
    H.rp([['El JSON DISV de esta malla contiene ', ''], ['ncpl', 'c'], [' 1134, ', ''],
      ['nvert', 'c'], [' 2527 y los arreglos ', ''], ['vertices', 'c'], [', ', ''],
      ['cell2d', 'c'], [' y ', ''], ['centroids', 'c'],
      [' que MODFLOW 6 necesita para describir una malla no estructurada.', '']]),
    H.spacer(),

    H.h2('5.9  Paso 9 — Exportar un modelo MODFLOW 6 para ModelMuse'),
    H.p('Este es el paso que convierte una malla en un modelo. La aplicación '
      + 'escribe una simulación MODFLOW 6 DISV completa con FloPy, muestreando '
      + 'sus rásteres de elevación en el centroide de cada celda.'),
    H.h3('Opcional: asociar antes los rásteres a una capa'),
    H.p('Seleccione una capa de refinamiento y pulse "Layer top/botm rasters…" '
      + 'para asociarle un ráster superior y otro inferior. Estos rellenan por '
      + 'adelantado el diálogo de exportación, para no tener que volver a '
      + 'buscarlos.'),
    ...H.figure('24_dialog_layer_rasters', 380,
      'Asociando rásteres de elevación a una capa de refinamiento.'),
    H.h3('El diálogo de exportación'),
    H.stepR([['Elija ', ''], ['File → Export ModelMuse MODFLOW 6 model…', 'b'], ['.', '']]),
    H.step('Fije el número de capas en 4.'),
    H.stepR([['Para la cota superior del modelo, pulse ', ''], ['Raster…', 'b'],
      [' y elija ', ''], ['modelTop.tif', 'c'], ['.', '']]),
    H.stepR([['Para cada base de capa, elija ', ''], ['bottomLy1.tif', 'c'],
      [' hasta ', ''], ['bottomLy4.tif', 'c'], ['.', '']]),
    H.step('Elija una carpeta de salida vacía y pulse OK.'),
    ...H.figure('25_dialog_modelmuse', 400,
      'El diálogo de exportación a ModelMuse, configurado para cuatro capas con '
      + 'un ráster para la cota superior y para cada base de capa.'),
    H.note('Constantes o rásteres.', 'Cualquier superficie admite las dos '
      + 'opciones. Escriba un número para una superficie plana, o señale un '
      + 'GeoTIFF para que se muestree en el centroide de cada celda. Puede '
      + 'combinarlas: una cota superior por ráster sobre bases de capa planas es '
      + 'una configuración habitual.'),
    H.spacer(120),
    H.h3('Qué obtiene'),
    H.p('La exportación escribe ocho archivos. Estas son las salidas reales de '
      + 'esta ejecución del tutorial:'),
    H.table(
      ['Archivo', 'Tamaño', 'Contenido'],
      [
        [[['mfsim.nam', 'c']], '345 B', 'Archivo de nombres de la simulación: es el que se le indica a ModelMuse'],
        [[['voronoiModel.disv', 'c']], '291 KB', 'La malla no estructurada: NLAY 4, NCPL 1134, NVERT 2527, más top y botm'],
        [[['voronoiModel.nam', 'c']], '266 B', 'Archivo de nombres del modelo de flujo subterráneo'],
        [[['voronoiModel.tdis', 'c']], '221 B', 'Discretización temporal'],
        [[['voronoiModel.ims', 'c']], '123 B', 'Configuración del solucionador iterativo'],
        [[['voronoiModel.npf', 'c']], '211 B', 'Paquete de flujo por propiedades de nodo'],
        [[['voronoiModel.ic', 'c']], '77 KB', 'Condiciones iniciales'],
        [[['voronoiModel.oc', 'c']], '245 B', 'Control de salida'],
      ],
      [2700, 1200, 6180]),
    H.spacer(120),
    H.ok('Comprobado.', 'En esta ejecución, las cuatro bases de capa salieron '
      + 'de los rásteres como −4,0, −7,5, −20,0 y −50,0 m, y la cota superior '
      + 'como 0,0 m, coincidiendo exactamente con los GeoTIFF de origen: el '
      + 'muestreo en los centroides hace lo que promete.'),
    H.spacer(120),
    H.h3('Importar en ModelMuse'),
    H.stepR([['En ModelMuse elija ', ''],
      ['File → Import → Import MODFLOW-6 Model…', 'b'], ['.', '']]),
    H.stepR([['Seleccione el archivo ', ''], ['mfsim.nam', 'c'], [' que escribió la exportación.', '']]),
    H.step('ModelMuse lee la malla DISV, las elevaciones de las capas y los paquetes, y a partir de ahí puede seguir construyendo el modelo.'),
    H.spacer(),

    H.h2('5.10  Paso 10 — Guardar el proyecto'),
    H.rp([['Use ', ''], ['File → Save project', 'b'], [' (', ''], ['Ctrl+S', 'c'],
      [') para escribir todo —CRS, límite, capas de refinamiento, vacíos, '
       + 'imágenes de fondo, opciones y la malla generada— en un único archivo ', ''],
      ['.mf6vor', 'c'],
      ['. El proyecto del tutorial ocupó unos 807 KB, la mayor parte de ellos la malla.', '']]),
    H.p('El título de la ventana muestra el nombre del archivo actual y un '
      + 'asterisco mientras haya cambios sin guardar. Al cerrar la aplicación, '
      + 'empezar un proyecto nuevo o abrir otro, se le pregunta si desea '
      + 'guardar primero.'),
    ...H.figure('28_main_final', H.PX, 'El proyecto del tutorial terminado, mallado y con su informe.'),
    H.pageBreak(),

    /* =========================================== 6. Datos propios == */
    H.h1('6. Trabajar con sus propios datos'),

    H.h2('6.1  Dibujar en lugar de importar'),
    H.p('Todo lo que puede importar, también puede dibujarlo. Resulta útil para '
      + 'esbozar un límite antes de que existan los datos SIG, o para añadir una '
      + 'zona de refinamiento alrededor de algo que ha visto en una imagen de fondo.'),
    H.stepR([['Elija el modo en el menú ', ''], ['Draw', 'b'],
      [' o en la barra de herramientas. Si es una capa de refinamiento, primero '
       + 'se le piden un nombre y un tamaño de celda.', '']]),
    H.step('Haga clic sobre el mapa para colocar vértices. Cada elemento terminado aparece de inmediato, y un contador sobre el lienzo lleva la cuenta de los que ha dibujado.'),
    H.step('Haga doble clic o pulse Enter para terminar la geometría actual. En modo punto, cada clic es ya un elemento completo.'),
    H.step('Siga añadiendo elementos a la misma capa y, cuando termine, elija "Finish current layer" (el botón del visto bueno) para confirmarla.'),
    H.step('"Cancel current layer" (el botón de la papelera) descarta todo lo dibujado en esta sesión.'),
    H.spacer(80),
    H.note('Acuérdese de terminar la capa.', 'Los elementos que dibuja no '
      + 'forman parte del proyecto hasta que termina la capa. Si la generación '
      + 'de la malla ignora algo que acaba de dibujar, compruebe que pulsó el '
      + 'botón del visto bueno.'),
    H.spacer(),

    H.h2('6.2  Polígonos de vacío'),
    H.p('Dibuje uno con Draw → New void polygon…, o importe un shapefile con '
      + 'File → Import void polygon shapefile…. Las celdas interiores a un vacío '
      + 'se eliminan, y las que quedan a caballo de su borde se recortan contra él.'),
    H.p('Los vacíos deben quedar dentro del límite del modelo. Como una celda '
      + 'DISV no puede tener un hueco, un vacío que perforaría una única celda '
      + 'grande elimina esa celda en lugar de atravesarla; por eso conviene que '
      + 'su tamaño de celda grueso sea menor que los vacíos que necesite '
      + 'representar.'),

    H.h2('6.3  Imágenes de fondo'),

    H.h3('6.3.1  Desde un archivo local'),
    H.p('La pestaña "From file" admite un GeoTIFF, o un PNG/JPG con su archivo '
      + 'de georreferenciación. Si no hay ninguno de los dos, se le pide la '
      + 'extensión directamente:'),
    ...H.figure('26_dialog_image_extent', 340,
      'Introduciendo a mano la extensión de una imagen, en coordenadas del proyecto.'),
    H.p('Si se equivoca en la extensión, la imagen aparecerá en el lugar '
      + 'equivocado; corríjalo eliminando la imagen y volviéndola a importar.'),

    H.h3('6.3.2  Imágenes satelitales en línea'),
    H.p('La pestaña "Online satellite map" descarga imágenes base gratuitas '
      + 'directamente de internet, así que no necesita conseguir y '
      + 'georreferenciar un archivo usted mismo:'),
    H.step('Elija un proveedor: Esri World Imagery (satélite) o Sentinel-2 '
      + 'Cloudless (EOX). Ambos son gratuitos y no requieren cuenta ni clave '
      + 'de API.'),
    H.step('Localice el área que necesita: escriba un nombre de lugar en '
      + 'Search, pulse "Fit to project extent" para ir directamente a la '
      + 'ubicación de su modelo, o desplácese (arrastrando) y haga zoom '
      + '(rueda del ratón o los botones +/−) manualmente.'),
    H.step('Opcionalmente, pulse "Draw export area" y arrastre un rectángulo '
      + 'sobre la región exacta que desea. Sin él, se usa la vista actual.'),
    H.step('Pulse "Export GeoTIFF…" para guardar la imagen en un archivo para '
      + 'más tarde, o "Add to project as background…" para guardarla y '
      + 'añadirla de inmediato.'),
    ...H.figure('30_dialog_online_imagery', H.PX,
      'El mapa satelital en línea, ajustado a la extensión del proyecto del '
      + 'tutorial. La línea de información bajo el mapa indica la fuente, el '
      + 'nivel de zoom, la resolución sobre el terreno y el número de '
      + 'teselas antes de descargar nada.'),
    H.p('Las teselas descargadas se combinan y se reproyectan de Web '
      + 'Mercator al sistema de coordenadas del proyecto, y se escriben como '
      + 'un GeoTIFF con el CRS incrustado — el mismo tipo de archivo que lee '
      + 'la pestaña "From file", de modo que puede volver a importarse en '
      + 'cualquier lugar más tarde.'),
    H.note('¿Sin CRS de proyecto todavía?', 'Si el proyecto no tiene un '
      + 'sistema de coordenadas definido, la imagen se reproyecta a una zona '
      + 'UTM detectada automáticamente, y se le pregunta si desea adoptar '
      + 'esa zona como el CRS del proyecto.'),
    H.note('Área demasiado grande.', 'Una estimación en vivo del número de '
      + 'teselas le avisa antes de descargar si el área elegida necesitaría '
      + 'demasiadas teselas al nivel de zoom actual. Haga zoom, o dibuje un '
      + 'área más pequeña, para continuar.'),
    H.note('Condiciones de uso.', 'Ambos proveedores son gratuitos para uso '
      + 'personal y de evaluación; revise sus condiciones antes de usar la '
      + 'imagen exportada con fines comerciales o de redistribuirla.'),

    H.h2('6.4  Medir distancias'),
    H.p('View → Measure distance (o el botón de la regla) convierte el cursor en '
      + 'una herramienta de medición. Haga clic en un punto inicial y después en '
      + 'uno final, y la distancia se muestra en la unidad de longitud del '
      + 'proyecto. Otro clic inicia una medición nueva; Esc cancela la que esté '
      + 'en curso. Es la forma más rápida de contrastar un tamaño de celda '
      + 'candidato con un elemento real antes de escribirlo.'),

    H.h2('6.5  Elegir los tamaños de refinamiento'),
    H.bulletR([['Trabaje del elemento más fino hacia fuera. ', 'b'],
      ['Decida cuánto debe medir la celda más pequeña —normalmente lo marca un '
       + 'pozo o un elemento estrecho— y deje que el multiplicador la lleve '
       + 'hasta el tamaño grueso.']]),
    H.bulletR([['Mantenga un rango razonable. ', 'b'],
      ['El tutorial va de 1 m a 20 m, un factor de 20. Bastante más allá de un '
       + 'factor de 50 debe esperar o bien una malla enorme o bien saltos '
       + 'visibles en el tamaño de celda.']]),
    H.bulletR([['Ordene las capas de gruesa a fina. ', 'b'],
      ['Los contornos con el refinamiento más grueso, después las áreas, '
       + 'después las líneas y por último los puntos. Es el orden que se usa en '
       + 'el capítulo 5.']]),
    H.bulletR([['Vigile el número de celdas. ', 'b'],
      ['Reducir a la mitad un tamaño objetivo multiplica aproximadamente por '
       + 'cuatro las celdas de esa zona. Genere, lea el informe, ajuste y vuelva '
       + 'a generar: en un modelo de este tamaño cada ejecución dura segundos.']]),
    H.bulletR([['Compruebe el área total en cada ejecución. ', 'b'],
      ['Debe coincidir con el área de su límite. Si no coincide, el recorte '
       + 'perdió celdas y hay algo mal en el polígono de límite.']]),
    H.pageBreak(),

    /* ====================================== 7. Resolución de problemas == */
    H.h1('7. Resolución de problemas'),
    H.table(
      ['Síntoma', 'Causa', 'Qué hacer'],
      [
        ['"Set or import a CRS first" al importar una capa de refinamiento',
          'Todavía no hay sistema de coordenadas.',
          'Defínalo en el panel CRS, o importe antes el polígono de límite para que se adopte su .prj.'],
        ['"This shapefile’s CRS differs from the project CRS"',
          'Sistemas de coordenadas mezclados.',
          'Reproyecte el archivo en su SIG al CRS del proyecto. La aplicación no lo reproyecta por usted.'],
        ['Un aviso de que un shapefile no tiene .prj',
          'No hay información de sistema de coordenadas junto al archivo.',
          'Se supone que el archivo ya está en el CRS del proyecto. Confírmelo, o los elementos quedarán desplazados.'],
        ['Una capa de refinamiento parece no tener efecto',
          'Antes de la 2.0.5, una capa que discurría más cerca del borde que su propio tamaño de celda se descartaba en silencio.',
          'Confirme con Help → About que está en la 2.0.5 o posterior. Si lo está, compruebe que la capa queda realmente dentro del límite y que su tamaño de celda es menor que el tamaño grueso.'],
        ['El límite no se importa',
          'Es multiparte, o el archivo contiene varios polígonos.',
          'Disuélvalo o recórtelo hasta dejar exactamente un polígono de una sola parte.'],
        ['Muchas más celdas de las esperadas, o una ejecución muy lenta',
          'El tamaño objetivo más fino es muy pequeño frente al grueso, o el multiplicador es bajo.',
          'Aumente el tamaño objetivo más fino, o suba el multiplicador hacia 1,5, y vuelva a generar.'],
        ['"Cells with short edges" da una cifra alarmante',
          'El umbral es grande respecto a su tamaño de celda objetivo más fino.',
          'Fíjelo en una fracción pequeña del objetivo más fino (vea la sección 5.7). Revise también "Shortest edge" y "Mean of min edges".'],
        ['El área total es menor que el área del límite',
          'Se perdieron celdas durante el recorte.',
          'Compruebe que el polígono de límite es válido y no se autointersecta; revise en el Log cuántas astillas se eliminaron.'],
        ['Vertices (nvert) muestra 0',
          'Todavía no se han calculado las propiedades DISV.',
          'Es lo esperado. Exporte el JSON DISV o el modelo para ModelMuse y vuelva a calcular el informe.'],
        ['No aparece la notificación de malla terminada',
          'Windows puede suprimir los avisos de aplicaciones sin firmar; el Asistente de concentración también los bloquea.',
          'El aviso emergente dentro de la aplicación aparece siempre: la 2.0.4 lo añadió precisamente por esto.'],
        ['Los elementos dibujados desaparecen',
          'La capa nunca se terminó.',
          'Pulse el botón del visto bueno (Finish current layer) para confirmar lo dibujado.'],
        ['Falla la generación de la malla',
          'Varias causas posibles.',
          'Lea el panel Log: contiene la traza completa y los mensajes de mf6Voronoi.'],
      ],
      [2800, 3200, 4080]),
    H.pageBreak(),

    /* ================================================ Apéndices == */
    H.h1('Apéndice A. Resumen de la ejecución del tutorial'),
    H.p('Valores de referencia de la ejecución que documenta este manual. Sus '
      + 'cifras coincidirán si sigue el capítulo 5 al pie de la letra.'),
    H.table(
      ['Concepto', 'Valor'],
      [
        ['Versión de la aplicación', '3.0.0'],
        ['Sistema de coordenadas', 'WGS 84 / UTM zona 31N (EPSG:32631), unidad metro'],
        ['Extensión del límite del modelo', '592.707,1 – 593.008,9 E; 5.762.469,6 – 5.762.760,0 N'],
        ['Tamaño del límite del modelo', '301,8 m × 290,5 m, área 44.293,7 m²'],
        ['Capas de refinamiento', 'modelGhb 10 m, site 4 m, hfb 3 m, drains 2 m, pointWell 1 m'],
        ['Tamaño de celda grueso (máximo)', '20 m'],
        ['Multiplicador de refinamiento', '1,3'],
        ['Solape de refinamientos', 'Activado'],
        ['Corrección de aristas por debajo de', '0,2 m'],
        ['Celdas generadas (ncpl)', '1134'],
        ['Vértices (nvert)', '2527'],
        ['Tiempo de generación', 'unos 3 segundos'],
        ['Área de celda (mín. / mediana / media / máx.)', '0,00 / 3,60 / 39,06 / 400,00 m²'],
        ['Área total de la malla', '44.293,75 m², igual al área del polígono de límite'],
        ['Vértices por celda (mín. / media / máx.)', '3 / 6,10 / 29'],
        ['Arista más corta / media de las mínimas', '0,0066 m / 1,2749 m'],
        ['Celdas con alguna arista menor de 0,2 m', '220 de 1134 (19 %)'],
        ['Astillas eliminadas por el recorte del borde', '20'],
        ['Exportación a ModelMuse', '4 capas; cota superior 0 m; bases −4, −7,5, −20 y −50 m'],
        ['Tamaño del archivo de proyecto', 'unos 807 KB'],
      ],
      [4000, 6080]),
    H.spacer(200),

    H.h1('Apéndice B. Archivos de salida'),
    H.table(
      ['Formato', 'Lo escribe', 'Qué es'],
      [
        [[['.mf6vor', 'c']], 'File → Save project',
          'Toda la sesión: CRS, límite, capas, vacíos, imágenes de fondo, opciones y la malla generada'],
        [[['.shp', 'c'], [' y asociados', '']], 'File → Export mesh shapefile…',
          'Las celdas Voronoi como shapefile de polígonos ESRI, con su .prj'],
        [[['.json', 'c'], [' (DISV)', '']], 'File → Export DISV properties…',
          'ncpl, nvert, vertices, cell2d, centroids y uniqueVerticesList'],
        [[['.csv', 'c'], [' / ', ''], ['.json', 'c']], 'File → Export quality report…',
          'Todas las métricas del informe de calidad'],
        ['Carpeta de modelo MODFLOW 6', 'File → Export ModelMuse MODFLOW 6 model…',
          'mfsim.nam más los archivos .disv, .nam, .tdis, .ims, .npf, .ic y .oc'],
      ],
      [2400, 3400, 4280]),
    H.spacer(200),

    H.h1('Apéndice C. Créditos y referencias'),
    H.p('mf6Voronoi Studio es una interfaz gráfica para el paquete mf6Voronoi '
      + 'de Hatari Labs, disponible en https://github.com/hatarilabs/mf6Voronoi.'),
    H.bullet('mf6Voronoi — Saul Montoya'),
    H.bullet('Desarrollo de la interfaz — An Ho Taylor'),
    H.spacer(80),
    H.p('Viva el Software Libre', { run: { italics: true, color: '5A6672' } }),
  ],
};
