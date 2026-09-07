/* mf6Voronoi Studio 3.0.0 — Quick Start Guide (English).
 * The seven steps, nothing else. The full reference is the User Manual.
 * Keep quickstart.es.js structurally in step with this file.
 */
'use strict';

module.exports = {
  meta: {
    appName: 'mf6Voronoi Studio',
    docTitle: 'Quick Start Guide',
    versionLine: 'Version 3.0.0',
    tagline: 'From shapefiles to a MODFLOW 6 grid in about ten minutes',
    headerText: 'mf6Voronoi Studio 3.0.0 — Quick Start Guide',
    description: 'Quick start guide for mf6Voronoi Studio 3.0.0',
    contentsTitle: 'Contents',
    figureWord: 'Figure',
    pageWord: 'Page',
    coverImage: '22_canvas_zoom_site',
    coverImageWidth: 560,
    coverTopSpace: 1100,
    coverNotes: [
      'Follow these seven steps on the Example folder that ships with the',
      'application. For the full reference, see the User Manual.',
    ],
    credits: ['mf6Voronoi — Saul Montoya', 'GUI developer — An Ho Taylor'],
    motto: 'Viva el Software Libre',
  },

  body: H => [
    ...H.cover(),
    ...H.contents(),

    /* ======================================================= before == */
    H.h1('1. Before you start'),
    H.p('mf6Voronoi Studio turns a model boundary and a handful of GIS features '
      + 'into an unstructured Voronoi grid for MODFLOW 6 — fine where you need '
      + 'detail, coarse where you do not.'),
    H.p('This guide walks one complete pass using the Example folder installed '
      + 'alongside the application. Work through it once and you will have '
      + 'produced a real grid and a ModelMuse-ready model.'),
    H.table(
      ['You need', 'Details'],
      [
        ['The application', 'mf6Voronoi Studio 3.0.0 (check with Help → About)'],
        ['The Example folder', 'Shipped with the application; used throughout this guide'],
        ['One projected CRS', 'In metres or feet. The Example data is EPSG:32631, in metres'],
        ['About ten minutes', 'The mesh in this guide generates in roughly three seconds'],
      ],
      [2600, 7480]),
    H.spacer(140),
    H.note('The one rule that matters.', 'Every file you import must be in the '
      + 'same projected coordinate system, and cell sizes are distances in that '
      + 'system’s unit. Geographic (latitude/longitude) data is rejected.'),
    H.spacer(),

    H.h2('The window'),
    H.p('The map is on the left; a scrolling column of panels is on the right, '
      + 'arranged top to bottom in the order you work through them.'),
    ...H.figure('01_main_empty', H.PX, 'The application on first launch.'),
    H.pageBreak(),

    /* ======================================================== steps == */
    H.h1('2. The seven steps'),

    H.h2('Step 1 — Set the coordinate system'),
    H.rp([['In the ', ''], ['Coordinate system (CRS)', 'b'], [' panel click ', ''],
      ['Set / change CRS…', 'b'], [', type ', ''], ['32631', 'c'],
      [' and click OK. The panel should then read "WGS 84 / UTM zone 31N '
       + '(EPSG:32631) — unit: meter".', '']]),
    ...H.figure('04_panel_crs_set', 430, 'The CRS panel once it is set.'),
    H.note('You can skip this step.', 'Importing the limit polygon first picks '
      + 'up the CRS from its .prj file automatically.'),
    H.spacer(),

    H.h2('Step 2 — Import the model limit'),
    H.rp([['Choose ', ''], ['File → Import limit polygon…', 'b'], [' and select ', ''],
      ['Example\\modelLimit.shp', 'c'],
      ['. The boundary appears in cyan and the map fits itself to it.', '']]),
    ...H.figure('05_limit_imported', H.PX, 'The model limit, loaded and fitted.'),
    H.rp([['It must be ', ''], ['exactly one single-part polygon', 'b'],
      ['. If yours is multipart, dissolve it in GIS first.', '']]),
    H.spacer(),

    H.h2('Step 3 — Add the refinement layers'),
    H.p('These are the features the grid should follow closely. For each one, '
      + 'choose File → Import refinement shapefile…, pick the file, then give '
      + 'it a name and a target cell size.'),
    ...H.figure('06_dialog_refinement_size', 320,
      'Naming a layer and setting its target cell size.'),
    H.p('Import these five, in this order — coarsest first, so cell sizes step '
      + 'down smoothly from the boundary to the wells:'),
    H.table(
      ['Shapefile', 'Name', 'Target cell size'],
      [
        [[['modelGhb.shp', 'c']], 'modelGhb', '10 m'],
        [[['site.shp', 'c']], 'site', '4 m'],
        [[['hfb.shp', 'c']], 'hfb', '3 m'],
        [[['drains.shp', 'c']], 'drains', '2 m'],
        [[['pointWell.shp', 'c']], 'pointWell', '1 m'],
      ],
      [3400, 3400, 3280]),
    H.spacer(120),
    ...H.figure('08_panel_layers', 430, 'All five layers loaded.'),
    H.p('You can draw layers instead of importing them — the Draw menu and the '
      + 'toolbar have point, line and polygon modes. Remember to click Finish '
      + 'layer (the check button) when you are done, or nothing is committed.'),
    H.spacer(),

    H.h2('Step 4 — Set the refinement options'),
    H.p('Scroll down to "Voronoi refinement options" and enter these four values:'),
    H.table(
      ['Option', 'Value', 'What it controls'],
      [
        ['Coarse (max) cell size', '20 m', 'The biggest cell, used far from every feature'],
        ['Refinement multiplier', '1.3', 'How fast cells grow outwards — about 30 % per ring'],
        ['Allow overlapping refinement', 'On', 'Lets refinement zones overlap instead of competing'],
        ['Fix short edges below', '0.2 m', 'Re-seeds cells with edges shorter than this'],
      ],
      [2900, 1300, 5880]),
    H.spacer(120),
    ...H.figure('10_panel_options', 430, 'The options for this run.'),
    H.p('A useful starting point on your own data: coarse size about 1/15 of '
      + 'the shorter side of your model, multiplier between 1.2 and 1.5.'),
    H.spacer(),

    H.h2('Step 5 — Generate the mesh'),
    H.rp([['Click ', ''], ['⚙  Generate Voronoi mesh', 'b'],
      [' in the Mesh panel (or the gear button on the toolbar), accept the '
       + 'default mesh name, and wait. This example finishes in about three '
       + 'seconds and tells you when it is done.', '']]),
    ...H.figure('23_popup_mesh_done', 380, 'The completion popup.'),
    ...H.figure('17_mesh_generated', H.PX,
      'The result: 1,134 cells, fine at the centre, coarse towards the corners.'),
    H.spacer(),

    H.h2('Step 6 — Check the mesh and the report'),
    H.p('Zoom in on the middle of the model. The cells should tighten smoothly '
      + 'towards each feature — no abrupt jump from coarse to fine.'),
    ...H.figure('22_canvas_zoom_site', 560,
      'Refinement tightening from 20 m cells to 1 m at the two wells (magenta).'),
    H.p('The quality report fills in on its own. Three numbers are worth a '
      + 'glance every time:'),
    H.table(
      ['Check', 'This run', 'What it means'],
      [
        ['Total area', '44,293.75 m²', 'Must equal your model limit area. It does here, exactly — nothing was lost when the mesh was clipped to the boundary.'],
        ['Cell area max', '400.00 m²', 'The 20 m coarse size squared, so the coarse setting was actually reached.'],
        ['Cells (ncpl)', '1,134', 'The size of your grid. If it is far larger than you expected, raise the finest target size or the multiplier.'],
      ],
      [1900, 1900, 6280]),
    H.spacer(120),
    ...H.figure('19_panel_report', 400, 'The full report for this run.'),
    H.note('Do not panic at "Cells with short edges".', 'The count is relative '
      + 'to the threshold you set. On this same mesh a 0.5 m threshold flags '
      + '60 % of cells; the 0.2 m used here flags 19 %. Set it to a small '
      + 'fraction of your finest target cell size and watch it as a trend '
      + 'between runs, not as a pass or fail.'),
    H.spacer(),

    H.h2('Step 7 — Export and save'),
    H.table(
      ['To get', 'Use', 'Result'],
      [
        ['The grid in GIS', 'File → Export mesh shapefile…',
          'An ESRI polygon shapefile with a .prj'],
        ['The raw DISV arrays', 'File → Export DISV properties (JSON)…',
          'ncpl, nvert, vertices, cell2d, centroids'],
        ['A MODFLOW 6 model', 'File → Export ModelMuse MODFLOW 6 model…',
          'Eight files including mfsim.nam and the .disv'],
        ['Your work back tomorrow', 'File → Save project (Ctrl+S)',
          'One .mf6vor file holding everything, mesh included'],
      ],
      [2400, 3600, 4080]),
    H.spacer(140),
    H.h3('The ModelMuse export in brief'),
    H.step('Choose File → Export ModelMuse MODFLOW 6 model…'),
    H.step('Set the number of layers to 4.'),
    H.stepR([['Set the model top to ', ''], ['modelTop.tif', 'c'],
      [' and the four layer bottoms to ', ''], ['bottomLy1.tif', 'c'], ['–', ''],
      ['bottomLy4.tif', 'c'], [' (click Raster… on each row).', '']]),
    H.step('Pick an empty output folder and click OK.'),
    H.stepR([['In ModelMuse: ', ''],
      ['File → Import → Import MODFLOW-6 Model…', 'b'], [' → select ', ''],
      ['mfsim.nam', 'c'], ['.', '']]),
    ...H.figure('25_dialog_modelmuse', 400,
      'The export dialog, set up for four layers with a raster for each surface.'),
    H.p('Any surface can be a plain number instead of a raster — type it in the '
      + 'field rather than browsing for a file.'),
    H.pageBreak(),

    /* ==================================================== reference == */
    H.h1('3. At a glance'),

    H.h2('Toolbar'),
    ...H.figure('15_toolbar', H.PX,
      'Left to right: Navigate · Limit · +Points · +Lines · +Polygons · +Void · '
      + 'Measure · Finish layer · Cancel layer · Generate mesh · Zoom in · '
      + 'Zoom out · Fit to data.'),
    H.p('The first seven are modes: one is active at a time, and its button '
      + 'stays pressed. Navigate is the default.'),

    H.h2('Keyboard and mouse'),
    H.table(
      ['Input', 'Does'],
      [
        [[['Ctrl+N', 'c'], [' / ', ''], ['Ctrl+O', 'c'], [' / ', ''], ['Ctrl+S', 'c']],
          'New project / Open project / Save project'],
        [[['Ctrl+Shift+S', 'c']], 'Save project as…'],
        [[['Enter', 'c']], 'Finish the shape you are drawing'],
        [[['Esc', 'c']], 'Cancel the shape or measurement in progress, otherwise deselect'],
        [[['Delete', 'c']], 'Remove the selected background image or void polygon'],
        ['Left-drag', 'Pan the map (in Navigate mode)'],
        ['Middle-drag', 'Pan the map (in any mode)'],
        ['Mouse wheel', 'Zoom in and out'],
        ['Double-click', 'Finish the shape you are drawing'],
      ],
      [2600, 7480]),
    H.spacer(160),

    H.h2('Five things that catch people out'),
    H.bulletR([['Drawn features vanish. ', 'b'],
      ['They are not committed until you click Finish layer (the check button).']]),
    H.bulletR([['A shapefile is refused. ', 'b'],
      ['Its CRS differs from the project’s. Re-project it in GIS — the '
       + 'application will not do it for you.']]),
    H.bulletR([['The limit will not load. ', 'b'],
      ['It must be exactly one single-part polygon.']]),
    H.bulletR([['Vertices (nvert) shows 0. ', 'b'],
      ['Expected — it stays 0 until you export the DISV properties or a '
       + 'ModelMuse model.']]),
    H.bulletR([['Far more cells than expected. ', 'b'],
      ['Your finest target size is very small relative to the coarse size. '
       + 'Halving a target size roughly quadruples the cells in that zone.']]),
    H.spacer(160),

    H.h2('Where to go next'),
    H.p('The User Manual covers every menu command, every sidebar panel, the '
      + 'drawing tools, void polygons, background images — including the new '
      + '"Online satellite map" tab for fetching a georeferenced satellite '
      + 'basemap directly from the internet — the measure tool, how to read '
      + 'each quality metric, and a troubleshooting table.'),
    H.spacer(80),
    H.p('mf6Voronoi Studio is a graphical front-end for the mf6Voronoi package '
      + 'by Hatari Labs: https://github.com/hatarilabs/mf6Voronoi'),
    H.spacer(80),
    H.p('Viva el Software Libre', { run: { italics: true, color: '5A6672' } }),
  ],
};
