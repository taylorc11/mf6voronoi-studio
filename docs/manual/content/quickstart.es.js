/* mf6Voronoi Studio 3.0.0 — Guía de Inicio Rápido (español).
 *
 * Traducción de quickstart.en.js; mantener ambos archivos en paralelo.
 * Los nombres de menús y botones se citan en inglés, como en la aplicación.
 */
'use strict';

module.exports = {
  meta: {
    appName: 'mf6Voronoi Studio',
    docTitle: 'Guía de Inicio Rápido',
    versionLine: 'Versión 3.0.0',
    tagline: 'De los shapefiles a una malla MODFLOW 6 en unos diez minutos',
    headerText: 'mf6Voronoi Studio 3.0.0 — Guía de Inicio Rápido',
    description: 'Guía de inicio rápido de mf6Voronoi Studio 3.0.0',
    contentsTitle: 'Contenido',
    figureWord: 'Figura',
    pageWord: 'Página',
    coverImage: '22_canvas_zoom_site',
    coverImageWidth: 560,
    coverTopSpace: 1100,
    coverNotes: [
      'Siga estos siete pasos sobre la carpeta Example que acompaña a la aplicación.',
      'Para la referencia completa, consulte el Manual de Usuario.',
    ],
    credits: ['mf6Voronoi — Saul Montoya', 'Desarrollo de la interfaz — An Ho Taylor'],
    motto: 'Viva el Software Libre',
  },

  body: H => [
    ...H.cover(),
    ...H.contents(),

    /* ======================================================= antes == */
    H.h1('1. Antes de empezar'),
    H.p('mf6Voronoi Studio convierte un límite de modelo y un puñado de '
      + 'elementos SIG en una malla Voronoi no estructurada para MODFLOW 6: '
      + 'fina donde necesita detalle y gruesa donde no.'),
    H.p('Esta guía recorre una pasada completa usando la carpeta Example que se '
      + 'instala junto a la aplicación. Al terminarla una vez habrá producido '
      + 'una malla real y un modelo listo para ModelMuse.'),
    H.note('Sobre el idioma y los números.',
      'La aplicación está en inglés y no se traduce, así que los nombres de '
      + 'menús y botones se citan aquí tal como aparecen en pantalla. Además, '
      + 'la interfaz muestra las cifras en formato anglosajón (1,134 celdas; '
      + '44,293.75 m²) mientras que este documento usa la convención española '
      + '(1134 celdas; 44.293,75 m²). Son los mismos valores.'),
    H.spacer(120),
    H.table(
      ['Necesita', 'Detalles'],
      [
        ['La aplicación', 'mf6Voronoi Studio 3.0.0 (compruébelo en Help → About)'],
        ['La carpeta Example', 'Se distribuye con la aplicación; se usa en toda esta guía'],
        ['Un CRS proyectado', 'En metros o en pies. Los datos de Example están en EPSG:32631, en metros'],
        ['Unos diez minutos', 'La malla de esta guía se genera en unos tres segundos'],
      ],
      [2600, 7480]),
    H.spacer(140),
    H.note('La única regla que importa de verdad.', 'Todos los archivos que '
      + 'importe deben estar en el mismo sistema de coordenadas proyectado, y '
      + 'los tamaños de celda son distancias en la unidad de ese sistema. Los '
      + 'datos geográficos (latitud/longitud) se rechazan.'),
    H.spacer(),

    H.h2('La ventana'),
    H.p('El mapa queda a la izquierda; a la derecha, una columna desplazable de '
      + 'paneles ordenados de arriba abajo según el orden en que se usan.'),
    ...H.figure('01_main_empty', H.PX, 'La aplicación recién arrancada.'),
    H.pageBreak(),

    /* ======================================================= pasos == */
    H.h1('2. Los siete pasos'),

    H.h2('Paso 1 — Definir el sistema de coordenadas'),
    H.rp([['En el panel ', ''], ['Coordinate system (CRS)', 'b'], [' pulse ', ''],
      ['Set / change CRS…', 'b'], [', escriba ', ''], ['32631', 'c'],
      [' y pulse OK. El panel debe mostrar entonces "WGS 84 / UTM zone 31N '
       + '(EPSG:32631) — unit: meter".', '']]),
    ...H.figure('04_panel_crs_set', 430, 'El panel CRS una vez definido.'),
    H.note('Puede saltarse este paso.', 'Al importar primero el polígono de '
      + 'límite, la aplicación toma automáticamente el CRS de su archivo .prj.'),
    H.spacer(),

    H.h2('Paso 2 — Importar el límite del modelo'),
    H.rp([['Elija ', ''], ['File → Import limit polygon…', 'b'], [' y seleccione ', ''],
      ['Example\\modelLimit.shp', 'c'],
      ['. El límite aparece en color cian y el mapa se ajusta a él.', '']]),
    ...H.figure('05_limit_imported', H.PX, 'El límite del modelo, cargado y ajustado.'),
    H.rp([['Debe ser ', ''], ['exactamente un polígono de una sola parte', 'b'],
      ['. Si el suyo es multiparte, disuélvalo antes en su SIG.', '']]),
    H.spacer(),

    H.h2('Paso 3 — Añadir las capas de refinamiento'),
    H.p('Son los elementos que la malla debe seguir de cerca. Para cada uno, '
      + 'elija File → Import refinement shapefile…, seleccione el archivo y '
      + 'dele un nombre y un tamaño de celda objetivo.'),
    ...H.figure('06_dialog_refinement_size', 320,
      'Nombrando una capa y fijando su tamaño de celda objetivo.'),
    H.p('Importe estas cinco, en este orden —de más gruesa a más fina— para que '
      + 'los tamaños de celda desciendan de forma gradual desde el contorno '
      + 'hasta los pozos:'),
    H.table(
      ['Shapefile', 'Nombre', 'Tamaño de celda objetivo'],
      [
        [[['modelGhb.shp', 'c']], 'modelGhb', '10 m'],
        [[['site.shp', 'c']], 'site', '4 m'],
        [[['hfb.shp', 'c']], 'hfb', '3 m'],
        [[['drains.shp', 'c']], 'drains', '2 m'],
        [[['pointWell.shp', 'c']], 'pointWell', '1 m'],
      ],
      [3400, 3400, 3280]),
    H.spacer(120),
    ...H.figure('08_panel_layers', 430, 'Las cinco capas cargadas.'),
    H.p('También puede dibujar las capas en lugar de importarlas: el menú Draw y '
      + 'la barra de herramientas tienen modos de punto, línea y polígono. '
      + 'Acuérdese de pulsar Finish layer (el botón del visto bueno) al '
      + 'terminar, o no se confirmará nada.'),
    H.spacer(),

    H.h2('Paso 4 — Ajustar las opciones de refinamiento'),
    H.p('Baje hasta "Voronoi refinement options" e introduzca estos cuatro valores:'),
    H.table(
      ['Opción', 'Valor', 'Qué controla'],
      [
        ['Coarse (max) cell size', '20 m', 'La celda mayor, usada lejos de todo elemento'],
        ['Refinement multiplier', '1,3', 'La rapidez con que crecen las celdas hacia fuera: un 30 % por anillo'],
        ['Allow overlapping refinement', 'Activado', 'Permite que las zonas de refinamiento se solapen en vez de competir'],
        ['Fix short edges below', '0,2 m', 'Vuelve a sembrar las celdas con aristas más cortas que este valor'],
      ],
      [2900, 1300, 5880]),
    H.spacer(120),
    ...H.figure('10_panel_options', 430, 'Las opciones de esta ejecución.'),
    H.p('Un buen punto de partida con sus propios datos: un tamaño grueso de '
      + 'alrededor de 1/15 del lado corto de su modelo y un multiplicador entre '
      + '1,2 y 1,5.'),
    H.spacer(),

    H.h2('Paso 5 — Generar la malla'),
    H.rp([['Pulse ', ''], ['⚙  Generate Voronoi mesh', 'b'],
      [' en el panel Mesh (o el botón del engranaje de la barra de '
       + 'herramientas), acepte el nombre de malla propuesto y espere. Este '
       + 'ejemplo termina en unos tres segundos y le avisa al acabar.', '']]),
    ...H.figure('23_popup_mesh_done', 380, 'El aviso de finalización.'),
    ...H.figure('17_mesh_generated', H.PX,
      'El resultado: 1134 celdas, finas en el centro y gruesas hacia las esquinas.'),
    H.spacer(),

    H.h2('Paso 6 — Revisar la malla y el informe'),
    H.p('Acérquese al centro del modelo. Las celdas deben cerrarse de forma '
      + 'gradual hacia cada elemento, sin saltos bruscos de grueso a fino.'),
    ...H.figure('22_canvas_zoom_site', 560,
      'El refinamiento se cierra desde celdas de 20 m hasta 1 m en los dos pozos (magenta).'),
    H.p('El informe de calidad se rellena solo. Conviene mirar siempre estas '
      + 'tres cifras:'),
    H.table(
      ['Comprobación', 'Esta ejecución', 'Qué significa'],
      [
        ['Total area', '44.293,75 m²', 'Debe coincidir con el área de su límite. Aquí coincide exactamente: no se perdió nada al recortar la malla contra el borde.'],
        ['Cell area max', '400,00 m²', 'El tamaño grueso de 20 m al cuadrado, así que el valor configurado se alcanzó de verdad.'],
        ['Cells (ncpl)', '1134', 'El tamaño de su malla. Si es mucho mayor de lo previsto, suba el tamaño objetivo más fino o el multiplicador.'],
      ],
      [1900, 1900, 6280]),
    H.spacer(120),
    ...H.figure('19_panel_report', 400, 'El informe completo de esta ejecución.'),
    H.note('No se alarme con "Cells with short edges".', 'El recuento es '
      + 'relativo al umbral que usted fija. Sobre esta misma malla, un umbral de '
      + '0,5 m señala el 60 % de las celdas; el de 0,2 m usado aquí señala el '
      + '19 %. Fíjelo en una fracción pequeña de su tamaño objetivo más fino y '
      + 'vigílelo como una tendencia entre ejecuciones, no como un aprobado o '
      + 'suspenso.'),
    H.spacer(),

    H.h2('Paso 7 — Exportar y guardar'),
    H.table(
      ['Para obtener', 'Use', 'Resultado'],
      [
        ['La malla en su SIG', 'File → Export mesh shapefile…',
          'Un shapefile de polígonos ESRI con su .prj'],
        ['Los arreglos DISV en bruto', 'File → Export DISV properties (JSON)…',
          'ncpl, nvert, vertices, cell2d y centroids'],
        ['Un modelo MODFLOW 6', 'File → Export ModelMuse MODFLOW 6 model…',
          'Ocho archivos, entre ellos mfsim.nam y el .disv'],
        ['Recuperar su trabajo mañana', 'File → Save project (Ctrl+S)',
          'Un único archivo .mf6vor con todo, malla incluida'],
      ],
      [2400, 3600, 4080]),
    H.spacer(140),
    H.h3('La exportación a ModelMuse, en breve'),
    H.step('Elija File → Export ModelMuse MODFLOW 6 model…'),
    H.step('Fije el número de capas en 4.'),
    H.stepR([['Ponga la cota superior en ', ''], ['modelTop.tif', 'c'],
      [' y las cuatro bases de capa en ', ''], ['bottomLy1.tif', 'c'], ['–', ''],
      ['bottomLy4.tif', 'c'], [' (pulse Raster… en cada fila).', '']]),
    H.step('Elija una carpeta de salida vacía y pulse OK.'),
    H.stepR([['En ModelMuse: ', ''],
      ['File → Import → Import MODFLOW-6 Model…', 'b'], [' → seleccione ', ''],
      ['mfsim.nam', 'c'], ['.', '']]),
    ...H.figure('25_dialog_modelmuse', 400,
      'El diálogo de exportación, configurado para cuatro capas con un ráster '
      + 'para cada superficie.'),
    H.p('Cualquier superficie puede ser un número en lugar de un ráster: '
      + 'escríbalo en el campo en vez de buscar un archivo.'),
    H.pageBreak(),

    /* =================================================== referencia == */
    H.h1('3. De un vistazo'),

    H.h2('Barra de herramientas'),
    ...H.figure('15_toolbar', H.PX,
      'De izquierda a derecha: Navigate · Limit · +Points · +Lines · +Polygons · '
      + '+Void · Measure · Finish layer · Cancel layer · Generate mesh · Zoom in · '
      + 'Zoom out · Fit to data.'),
    H.p('Los siete primeros son modos: solo hay uno activo a la vez y su botón '
      + 'permanece pulsado. Navigate es el modo por defecto.'),

    H.h2('Teclado y ratón'),
    H.table(
      ['Acción', 'Hace'],
      [
        [[['Ctrl+N', 'c'], [' / ', ''], ['Ctrl+O', 'c'], [' / ', ''], ['Ctrl+S', 'c']],
          'Nuevo proyecto / Abrir proyecto / Guardar proyecto'],
        [[['Ctrl+Shift+S', 'c']], 'Guardar proyecto como…'],
        [[['Enter', 'c']], 'Termina la geometría que está dibujando'],
        [[['Esc', 'c']], 'Cancela la geometría o medición en curso; si no hay ninguna, deselecciona'],
        [[['Supr', 'c']], 'Elimina la imagen de fondo o el polígono de vacío seleccionado'],
        ['Arrastrar con el botón izquierdo', 'Desplaza el mapa (en modo Navigate)'],
        ['Arrastrar con el botón central', 'Desplaza el mapa (en cualquier modo)'],
        ['Rueda del ratón', 'Acerca y aleja la vista'],
        ['Doble clic', 'Termina la geometría que está dibujando'],
      ],
      [2600, 7480]),
    H.spacer(160),

    H.h2('Cinco tropiezos habituales'),
    H.bulletR([['Los elementos dibujados desaparecen. ', 'b'],
      ['No quedan confirmados hasta que pulsa Finish layer (el botón del visto bueno).']]),
    H.bulletR([['Se rechaza un shapefile. ', 'b'],
      ['Su CRS no coincide con el del proyecto. Reproyéctelo en su SIG: la '
       + 'aplicación no lo hará por usted.']]),
    H.bulletR([['El límite no se carga. ', 'b'],
      ['Debe ser exactamente un polígono de una sola parte.']]),
    H.bulletR([['Vertices (nvert) muestra 0. ', 'b'],
      ['Es lo normal: sigue en 0 hasta que exporta las propiedades DISV o un '
       + 'modelo para ModelMuse.']]),
    H.bulletR([['Muchas más celdas de las esperadas. ', 'b'],
      ['Su tamaño objetivo más fino es muy pequeño frente al grueso. Reducir a '
       + 'la mitad un tamaño objetivo multiplica por cuatro las celdas de esa zona.']]),
    H.spacer(160),

    H.h2('Dónde seguir'),
    H.p('El Manual de Usuario cubre todos los comandos de menú, todos los '
      + 'paneles laterales, las herramientas de dibujo, los polígonos de vacío, '
      + 'las imágenes de fondo —incluida la nueva pestaña "Online satellite '
      + 'map" para obtener un mapa base satelital georreferenciado '
      + 'directamente de internet—, la herramienta de medición, cómo leer '
      + 'cada métrica de calidad y una tabla de resolución de problemas.'),
    H.spacer(80),
    H.p('mf6Voronoi Studio es una interfaz gráfica para el paquete mf6Voronoi '
      + 'de Hatari Labs: https://github.com/hatarilabs/mf6Voronoi'),
    H.spacer(80),
    H.p('Viva el Software Libre', { run: { italics: true, color: '5A6672' } }),
  ],
};
