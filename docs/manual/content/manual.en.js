/* mf6Voronoi Studio 3.0.0 — User Manual (English).
 * Layout lives in ../docbuild.js; this file is content only.
 * Keep manual.es.js structurally in step with this file.
 */
'use strict';

module.exports = {
  meta: {
    appName: 'mf6Voronoi Studio',
    docTitle: 'User Manual',
    versionLine: 'Version 3.0.0',
    tagline: 'Create, edit, refine and export MODFLOW 6 DISV Voronoi meshes',
    headerText: 'mf6Voronoi Studio 3.0.0 — User Manual',
    description: 'User manual for mf6Voronoi Studio 3.0.0',
    contentsTitle: 'Contents',
    figureWord: 'Figure',
    pageWord: 'Page',
    coverImage: '17_mesh_generated',
    coverNotes: [
      'Every screenshot and every number in this manual was produced by running',
      'mf6Voronoi Studio 3.0.0 on the Example dataset shipped with the application.',
    ],
    credits: ['mf6Voronoi — Saul Montoya', 'GUI developer — An Ho Taylor'],
    motto: 'Viva el Software Libre',
  },

  body: H => [
    ...H.cover(),
    ...H.contents(),

    /* ============================================== 1. Introduction == */
    H.h1('1. Introduction'),

    H.h2('1.1  What mf6Voronoi Studio does'),
    H.p('mf6Voronoi Studio is a Windows desktop application for building '
      + 'unstructured Voronoi groundwater model grids. You give it a model '
      + 'boundary and a set of features you want the grid to follow closely — '
      + 'wells, drains, rivers, a site footprint, a barrier — and it generates '
      + 'a Voronoi tessellation that is fine near those features and '
      + 'progressively coarser away from them.'),
    H.p('It is a graphical front-end for the mf6Voronoi Python package by '
      + 'Hatari Labs. Everything the package can do headlessly, you can do here '
      + 'by pointing and clicking, and you can inspect the result on a map '
      + 'before you commit to it.'),
    H.table(
      ['What you need', 'How the application delivers it'],
      [
        ['Create, edit and export a DISV Voronoi grid',
          'Generate with mf6Voronoi; edit layers live; export shapefile, DISV JSON or a ModelMuse model'],
        ['Handle many refinement layers',
          'Unlimited layers, each with its own target cell size, visibility toggle and colour'],
        ['Import GIS data',
          'A model limit polygon plus point, line and polygon refinement shapefiles'],
        ['Import a background image',
          'GeoTIFF, or PNG/JPG with a world file, or a manually entered extent'],
        ['Refine with points, lines and polygons',
          'Import them, or draw them interactively on the map'],
        ['Progressive refinement control',
          'Coarse cell size, growth multiplier, overlapping refinement, short-edge fixing'],
        ['Exclude areas from the grid',
          'Void polygons — a lake or an excluded block where no cells are generated'],
        ['Check grid quality before you model',
          'A live cell-count and quality report you can export as CSV or JSON'],
        ['Get the grid into MODFLOW 6',
          'A complete FloPy-written MODFLOW 6 DISV simulation that ModelMuse can import'],
        ['Save and resume work',
          'The whole session, mesh included, in one .mf6vor project file'],
      ],
      [3200, 6880]),
    H.spacer(),

    H.h2('1.2  How the grid is built'),
    H.p('Three things control the result. Understanding them is most of what '
      + 'you need to use the application well.'),
    H.bulletR([['The model limit. ', 'b'],
      ['A single polygon that bounds the grid. Exactly one single-part polygon '
       + '— no multipart features, no holes (use void polygons for holes).']]),
    H.bulletR([['Refinement layers. ', 'b'],
      ['Points, lines or polygons, each carrying a target cell size. Near a '
       + 'layer’s features, cells are generated at roughly that size.']]),
    H.bulletR([['The coarse cell size and the multiplier. ', 'b'],
      ['Away from every refinement feature, cells grow towards the coarse '
       + '(maximum) size. The multiplier sets how fast they grow: 1.3 means '
       + 'each successive ring of cells is about 30 % larger than the last. A '
       + 'small multiplier gives a smoother, larger grid; a large one gives a '
       + 'smaller, blockier grid.']]),
    H.spacer(80),
    H.p('The application seeds points according to those rules, builds the '
      + 'Voronoi tessellation, clips it to your model limit, and hands you the '
      + 'cells.'),

    H.h2('1.3  What is new in version 3.0.0'),
    H.p('3.0.0 adds a second way to get a background image: instead of only '
      + 'importing a file, you can now pan and zoom a live online satellite '
      + 'map, pick the area you need, and add it directly as a background — '
      + 'or export it as a georeferenced GeoTIFF to keep and re-import later.'),
    H.p('File → Add background image (file or online map)… now opens a dialog '
      + 'with two tabs. "From file" is the previous import flow, unchanged. '
      + '"Online satellite map" is new: choose a free imagery provider (Esri '
      + 'World Imagery or Sentinel-2 Cloudless), search for a place or fit to '
      + 'your project extent, optionally drag out the exact area you want, and '
      + 'click "Add to project as background…" or "Export GeoTIFF…". The image '
      + 'is downloaded, reprojected into the project’s coordinate system (or '
      + 'an automatically detected UTM zone if none is set yet), and written as '
      + 'a normal GeoTIFF with an embedded CRS — no world file needed.'),
    H.note('Free imagery, personal / evaluation use.', 'Both providers are '
      + 'free and need no API key, but review their terms before using the '
      + 'exported imagery commercially or redistributing it.'),
    H.spacer(),
    H.p('Earlier releases fixed a refinement bug that bit a very common '
      + 'real-world case: if a refinement feature ran closer to the model '
      + 'boundary than its own target cell size — a general-head boundary line '
      + 'following the edge of the domain, for instance — mf6Voronoi silently '
      + 'discarded every seed point for that layer, with no warning (2.0.5). '
      + 'The tutorial in Chapter 5 exercises exactly this case: the modelGhb '
      + 'layer runs along the model edge and is correctly refined.'),
    H.ok('Verified.', 'In the tutorial run, the clipped mesh area came to '
      + '44,293.75 m² — identical to the area of the model limit polygon, so '
      + 'the clip leaves no gaps and no overlaps.'),
    H.spacer(),
    H.p('Earlier releases in the 2.0 line also added: multiple background '
      + 'images (2.0.3), a mesh-finished notification and an in-app completion '
      + 'popup (2.0.3 / 2.0.4), a measure-distance tool, "Save project as…" and '
      + 'an unsaved-changes prompt (2.0.2), void polygons (2.0.1), and a '
      + 'rebuilt hardware-accelerated map canvas with a dark interface (2.0.0).'),

    H.h2('1.4  Requirements and limitations'),
    H.bullet('Windows. The application ships as an installer, a portable ZIP, or Python source.'),
    H.bulletR([['All inputs must share one projected coordinate system, in metres or feet. ', 'b'],
      ['Geographic (latitude/longitude) systems are rejected, because cell '
       + 'sizes are expressed as a distance.']]),
    H.bullet('The model limit must be exactly one single-part polygon.'),
    H.bullet('Multipart refinement features are exploded into single parts on import.'),
    H.bullet('A DISV cell cannot contain a hole, so void polygons remove or clip cells rather than perforating them.'),
    H.pageBreak(),

    /* ========================================= 2. Getting started == */
    H.h1('2. Installation and first launch'),

    H.h2('2.1  Installing'),
    H.table(
      ['Option', 'What you get', 'Best for'],
      [
        [[['mf6VoronoiStudio-3.0.0-Setup.exe', 'c']],
          'Installs to Program Files with Start-menu shortcuts and an uninstaller',
          'Normal use on your own machine'],
        ['Portable ZIP', 'A self-contained folder — unzip and run, nothing installed',
          'USB sticks, locked-down PCs'],
        ['Python source', 'Run directly from the repository with your own Python',
          'Development and customisation'],
      ],
      [3000, 4200, 2880]),
    H.spacer(120),
    H.rp([['To run from source you need Python 3.10–3.12 (64-bit). Install the '
      + 'dependencies with ', ''], ['pip install -r requirements.txt', 'c'],
      [' and start the application with ', ''],
      ['python mf6voronoi_gui.py', 'c'], ['.', '']]),
    H.note('Tip.', 'If Windows offers you the Microsoft Store when you type '
      + '"python", real Python is not installed yet. Install it from '
      + 'python.org, tick "Add python.exe to PATH", and if necessary turn off '
      + 'the Store aliases under Settings → Apps → Advanced app settings → App '
      + 'execution aliases. On Windows you can double-click CHECK_PYTHON.bat to '
      + 'confirm, then build_windows.bat.'),
    H.spacer(),

    H.h2('2.2  The main window'),
    H.p('The application opens with an empty project. Nothing is loaded, no '
      + 'coordinate system is set, and the map is blank.'),
    ...H.figure('01_main_empty', H.PX,
      'mf6Voronoi Studio 3.0.0 on first launch, with an empty project.'),
    H.p('The window has four regions:'),
    H.bulletR([['The menu bar ', 'b'], ['— File, Draw, View and Help (Chapter 3).']]),
    H.bulletR([['The toolbar ', 'b'],
      ['— one-click access to the drawing modes, mesh generation and zoom controls.']]),
    H.bulletR([['The map canvas ', 'b'],
      ['— on the left, taking most of the window. Pan, zoom, draw and select here.']]),
    H.bulletR([['The sidebar ', 'b'],
      ['— on the right, a scrolling column of panels that runs top to bottom in '
       + 'the order you normally work: coordinate system, background images, '
       + 'refinement layers, void polygons, refinement options, mesh, quality '
       + 'report, log (Chapter 4).']]),
    H.spacer(80),
    H.p('The sidebar is taller than the window, so scroll it to reach the lower panels.'),
    ...H.figure('29_main_sidebar_scrolled', H.PX,
      'The same window with the sidebar scrolled down to the refinement '
      + 'options, Mesh, quality report and Log panels.'),
    H.pageBreak(),

    /* ================================================== 3. Menus == */
    H.h1('3. Menu, toolbar and input reference'),

    H.h2('3.1  File menu'),
    ...H.figure('11_menu_file', H.PX, 'The File menu.'),
    H.table(
      ['Command', 'Shortcut', 'What it does'],
      [
        ['New project', 'Ctrl+N', 'Clears everything and starts over. Prompts first if there are unsaved changes.'],
        ['Open project…', 'Ctrl+O', 'Opens a saved .mf6vor project, including its generated mesh.'],
        ['Save project', 'Ctrl+S', 'Saves to the current file. Asks for a location the first time only.'],
        ['Save project as…', 'Ctrl+Shift+S', 'Saves to a new file and makes that the current file.'],
        ['Import limit polygon…', '', 'Loads the model boundary from a polygon shapefile. Adopts the CRS from the .prj file if no CRS is set.'],
        ['Import refinement shapefile…', '', 'Loads a point, line or polygon shapefile as a refinement layer; asks for a name and target cell size.'],
        ['Add background image (file or online map)…', '', 'Opens a dialog with two tabs: a local-file import, or an interactive online satellite map. Repeatable — you can load several.'],
        ['Remove background image', '', 'Removes the selected background image.'],
        ['Import void polygon shapefile…', '', 'Loads one or more polygons inside which no cells will be generated.'],
        ['Export mesh shapefile…', '', 'Writes the generated cells as an ESRI polygon shapefile, with a .prj.'],
        ['Export DISV properties (JSON)…', '', 'Writes the DISV arrays — vertices, cell2d, ncpl, nvert — as JSON.'],
        ['Export quality report…', '', 'Writes the current report as CSV or JSON.'],
        ['Export ModelMuse MODFLOW 6 model…', '', 'Writes a complete MODFLOW 6 DISV simulation you can import into ModelMuse.'],
        ['Quit', '', 'Closes the application, prompting if there are unsaved changes.'],
      ],
      [3100, 1500, 5480]),
    H.pageBreak(),

    H.h2('3.2  Draw menu'),
    H.p('The Draw menu selects what a click on the map does. Only one mode is '
      + 'active at a time, and the matching toolbar button stays pressed while it is.'),
    ...H.figure('12_menu_draw', H.PX, 'The Draw menu.'),
    H.table(
      ['Command', 'What it does'],
      [
        ['Navigate (pan/zoom)', 'The default. Clicking and dragging pans the map; clicking selects items.'],
        ['Draw limit polygon', 'Digitises the model boundary directly on the map instead of importing it.'],
        ['New point refinement layer…', 'Asks for a name and cell size, then every click drops a refinement point.'],
        ['New polyline refinement layer…', 'Asks for a name and cell size, then digitises one or more polylines.'],
        ['New polygon refinement layer…', 'Asks for a name and cell size, then digitises one or more polygons.'],
        ['New void polygon…', 'Digitises a polygon inside which no cells will be generated.'],
        ['Finish current layer', 'Commits the features drawn so far and returns to Navigate.'],
        ['Cancel current layer', 'Discards everything drawn in the current session and returns to Navigate.'],
      ],
      [3400, 6680]),
    H.spacer(140),

    H.h2('3.3  View menu'),
    ...H.figure('13_menu_view', H.PX, 'The View menu.'),
    H.table(
      ['Command', 'What it does'],
      [
        ['Zoom to data', 'Fits everything loaded — limit, layers, mesh, background images — into the window.'],
        ['Zoom in / Zoom out', 'Steps the zoom level. The mouse wheel does the same, continuously.'],
        ['Measure distance', 'Click a start point then an end point to read the distance in the project’s length unit. Click again to start a new measurement; Esc cancels one in progress.'],
      ],
      [3400, 6680]),
    H.spacer(140),

    H.h2('3.4  Help menu'),
    H.p('Help contains a single command, About, which reports the exact version '
      + 'you are running — useful when checking whether you have the 3.0.0 '
      + 'online-imagery tab or the 2.0.5 boundary-refinement fix.'),
    ...H.figure('27_dialog_about', 330, 'Help → About confirms the running version.'),
    H.pageBreak(),

    H.h2('3.5  Toolbar'),
    ...H.figure('15_toolbar', H.PX,
      'The toolbar. The first seven buttons are modes and stay pressed while active.'),
    H.table(
      ['#', 'Button', 'Equivalent menu command'],
      [
        ['1', 'Navigate (arrow)', 'Draw → Navigate (pan/zoom)'],
        ['2', 'Limit', 'Draw → Draw limit polygon'],
        ['3', '+Points', 'Draw → New point refinement layer…'],
        ['4', '+Lines', 'Draw → New polyline refinement layer…'],
        ['5', '+Polygons', 'Draw → New polygon refinement layer…'],
        ['6', '+Void', 'Draw → New void polygon…'],
        ['7', 'Measure', 'View → Measure distance'],
        ['8', 'Finish layer (check)', 'Draw → Finish current layer'],
        ['9', 'Cancel layer (bin)', 'Draw → Cancel current layer'],
        ['10', 'Generate mesh (gear)', 'The "Generate Voronoi mesh" button in the Mesh panel'],
        ['11', 'Zoom in', 'View → Zoom in'],
        ['12', 'Zoom out', 'View → Zoom out'],
        ['13', 'Fit to data', 'View → Zoom to data'],
      ],
      [700, 3300, 6080]),
    H.spacer(140),

    H.h2('3.6  Mouse and keyboard on the map'),
    H.table(
      ['Input', 'In Navigate mode', 'While drawing'],
      [
        ['Left-click', 'Selects an item (a background image, a void)', 'Adds a vertex — or, in point mode, drops a point immediately'],
        ['Left-drag', 'Pans the map', '—'],
        ['Middle-drag', 'Pans the map', 'Pans the map (works in every mode)'],
        ['Double-click', '—', 'Adds a final vertex and finishes the current shape'],
        ['Mouse wheel', 'Zooms in and out', 'Zooms in and out'],
        [[['Enter', 'c']], '—', 'Finishes the current shape'],
        [[['Esc', 'c']], 'Deselects everything', 'Cancels the shape in progress, or a measurement in progress'],
        [[['Delete', 'c'], [' / ', ''], ['Backspace', 'c']], 'Removes the selected background image or void polygon', '—'],
      ],
      [1900, 3900, 4280]),
    H.spacer(140),

    H.h2('3.7  Keyboard shortcuts'),
    H.table(
      ['Shortcut', 'Command'],
      [
        [[['Ctrl+N', 'c']], 'New project'],
        [[['Ctrl+O', 'c']], 'Open project…'],
        [[['Ctrl+S', 'c']], 'Save project'],
        [[['Ctrl+Shift+S', 'c']], 'Save project as…'],
        [[['Enter', 'c']], 'Finish the shape being drawn'],
        [[['Esc', 'c']], 'Cancel the shape or measurement in progress, otherwise deselect'],
        [[['Delete', 'c']], 'Remove the selected background image or void polygon'],
      ],
      [2400, 7680]),
    H.pageBreak(),

    /* ================================================= 4. Panels == */
    H.h1('4. The sidebar panels'),

    H.h2('4.1  Coordinate system (CRS)'),
    H.p('The first thing to set, and the one that blocks everything else. Cell '
      + 'sizes are distances, so the project needs a projected coordinate '
      + 'system whose unit is metres or feet. Until a CRS is set, the panel '
      + 'shows "No CRS set" and refinement imports are refused.'),
    ...H.figure('02_panel_crs_empty', 430, 'The CRS panel before a coordinate system is set.'),
    ...H.figure('04_panel_crs_set', 430,
      'After setting EPSG:32631. The panel names the system and confirms its length unit.'),
    H.note('Important.', 'Every shapefile you import must use this exact '
      + 'coordinate system. The application reads a CRS automatically from a '
      + 'shapefile’s .prj file, and refuses any file whose CRS differs from the '
      + 'project’s. Re-project mismatched data in GIS first.'),
    H.spacer(),

    H.h2('4.2  Background images'),
    H.p('Optional georeferenced imagery drawn beneath the map — an aerial '
      + 'photo, a scanned map, a published figure, or a satellite basemap '
      + 'fetched online. Add as many as you need; each gets its own row with a '
      + 'visibility checkbox. Select an image by clicking it on the map, then '
      + 'remove it with the panel’s Remove button, the Delete key, or File → '
      + 'Remove background image. Press Esc or click empty space to deselect.'),
    H.p('The panel’s Add… button (and File → Add background image (file or '
      + 'online map)…) opens a dialog with two tabs:'),
    H.bulletR([['From file. ', 'b'],
      ['A GeoTIFF carries its own extent. A plain PNG or JPG needs either a '
       + 'world file alongside it or an extent you type in by hand.']]),
    H.bulletR([['Online satellite map. ', 'b'],
      ['Pan and zoom a free imagery provider, search for a place, or fit to '
       + 'the current project extent, then add it to the project or export it '
       + 'as a GeoTIFF. See section 6.3 for the full workflow.']]),

    H.h2('4.3  Refinement layers'),
    H.p('The heart of the tool. Each row shows a visibility checkbox, the layer '
      + 'name, its geometry type and its target cell size, colour-coded to '
      + 'match the map.'),
    ...H.figure('08_panel_layers', 430,
      'The refinement layers panel with the five layers used in the Chapter 5 tutorial.'),
    H.bulletR([['Edit size… ', 'b'], ['changes a layer’s target cell size (and name).']]),
    H.bulletR([['Delete ', 'b'], ['removes the selected layer.']]),
    H.bulletR([['Layer top/botm rasters… ', 'b'],
      ['attaches elevation rasters to the layer, which then pre-fill the '
       + 'ModelMuse export dialog.']]),
    H.spacer(80),
    H.p('Unchecking a layer only hides it on the map. It still takes part in '
      + 'meshing — delete it if you want it excluded.'),

    H.h2('4.4  Void polygons'),
    H.p('Polygons inside the model limit where no cells are generated — a lake, '
      + 'a building footprint, an area outside the aquifer. Draw them, or '
      + 'import them from a shapefile.'),
    ...H.figure('09_panel_voids', 430, 'The void polygons panel (empty in the tutorial project).'),
    H.p('mf6Voronoi has no native concept of a hole, so the application seeds '
      + 'points along each void’s boundary to get a clean edge, then removes or '
      + 'clips the cells that fall inside it. Cells are never left with a hole '
      + 'in them, because the DISV format cannot represent one.'),

    H.h2('4.5  Voronoi refinement options'),
    ...H.figure('10_panel_options', 430, 'The refinement options, set as used in the tutorial.'),
    H.table(
      ['Option', 'Meaning', 'Guidance'],
      [
        ['Coarse (max) cell size',
          'The largest cell the grid will produce, used far from every refinement feature.',
          'Start around 1/15 to 1/20 of the shorter side of your model.'],
        ['Refinement multiplier',
          'How fast cells grow between a refinement feature and the coarse size. 1.3 means about 30 % per ring.',
          'Range 1.0–10.0. 1.2–1.5 is the usual working range. Lower is smoother but produces more cells.'],
        ['Allow overlapping refinement',
          'Lets refinement zones from different layers overlap instead of competing.',
          'Leave it on unless you have a specific reason not to.'],
        ['Fix short edges below',
          'After the first tessellation, cells with an edge shorter than this are re-seeded and the mesh is regenerated. 0 disables the pass.',
          'A small fraction of your finest target cell size. See the caution in section 5.7.'],
      ],
      [2500, 4200, 3380]),
    H.spacer(140),

    H.h2('4.6  Mesh'),
    ...H.figure('18_panel_mesh', 430, 'The Mesh panel after a successful run.'),
    H.p('"Generate Voronoi mesh" runs the meshing in the background, so the '
      + 'window stays responsive and the Log panel fills in as it goes. The '
      + 'label beneath reports the cell count. "Show generated mesh" hides the '
      + 'mesh without deleting it — useful when you want to keep editing '
      + 'refinement layers over a cluttered map.'),

    H.h2('4.7  Cell-count / quality report'),
    H.p('Fills in automatically when a mesh finishes, and can be recomputed at '
      + 'any time. "Save report…" writes it as CSV or JSON.'),
    ...H.figure('19_panel_report', 400, 'The quality report from the tutorial mesh.'),
    H.table(
      ['Metric', 'What it tells you'],
      [
        ['Cells (ncpl)', 'Number of cells per layer — the size of your model grid.'],
        ['Vertices (nvert)', 'Number of unique vertices. Shows 0 until the DISV properties have been computed (see the note in section 5.7).'],
        ['Cell area min / max / mean / median', 'The spread of cell sizes. Compare max against your coarse setting and min against your finest target size.'],
        ['Total area', 'Should equal the area of your model limit polygon. A shortfall means the clip lost cells.'],
        ['Vertices per cell', 'Typical Voronoi cells have 5–7 sides. A high maximum points at over-refinement transitions.'],
        ['Shortest edge / Mean of min edges', 'The smallest edge anywhere, and the average across cells. Very short edges can stiffen a MODFLOW solution.'],
        ['Short-edge threshold', 'The value from "Fix short edges below" — the yardstick for the row beneath.'],
        ['Cells with short edges', 'How many cells have an edge below that threshold. Shown in red when non-zero.'],
      ],
      [3200, 6880]),
    H.spacer(140),

    H.h2('4.8  Log'),
    H.p('A running transcript of everything the application and the mf6Voronoi '
      + 'package report — point-cloud progress, the short-edge fixing pass, '
      + 'clipping, warnings and full tracebacks if something fails. Read it '
      + 'first when a run does not do what you expected.'),
    ...H.figure('20_panel_log', 430, 'The Log panel at the end of the tutorial run.'),
    H.pageBreak(),

    /* =============================================== 5. Tutorial == */
    H.h1('5. Tutorial: meshing the Example dataset'),
    H.p('This chapter walks the complete workflow using the Example folder that '
      + 'ships with the application. Everything shown here was produced by an '
      + 'actual run — the screenshots, the cell counts and the report figures '
      + 'all come from the same session.'),

    H.h2('5.0  What is in the Example folder'),
    H.p('A small site model in WGS 84 / UTM zone 31N (EPSG:32631), with metres '
      + 'as its length unit. The model limit spans roughly 302 m east–west by '
      + '291 m north–south, enclosing 44,293.7 m².'),
    H.table(
      ['File', 'Geometry', 'Features', 'Role in this tutorial'],
      [
        [[['modelLimit.shp', 'c']], 'Polygon', '1', 'The model boundary'],
        [[['modelGhb.shp', 'c']], 'Line', '2', 'General-head boundary along the model edge — refinement layer'],
        [[['site.shp', 'c']], 'Polygon', '1', 'Site footprint — refinement layer'],
        [[['hfb.shp', 'c']], 'Line', '1', 'Horizontal-flow barrier — refinement layer'],
        [[['drains.shp', 'c']], 'Line', '2', 'Drains — refinement layer'],
        [[['pointWell.shp', 'c']], 'Point', '2', 'Pumping wells — refinement layer'],
        [[['crossSection.shp', 'c']], 'Line', '1', 'Cross-section trace (not used for refinement here)'],
        [[['rasterExtension.shp', 'c']], 'Polygon', '1', 'Extent of the DEM (not used for refinement)'],
        [[['modelTop.tif', 'c']], 'Raster', '106×99', 'Model top elevation, 0 m'],
        [[['bottomLy1–4.tif', 'c']], 'Raster', '106×99', 'Layer bottoms at −4, −7.5, −20 and −50 m'],
        [[['modelDem.tif', 'c']], 'Raster', '121×119', 'Ground surface DEM, 1 m'],
      ],
      [2400, 1500, 1300, 4880]),
    H.spacer(120),
    H.ok('Note.', 'modelGhb runs right along the model boundary, closer to the '
      + 'edge than its own 10 m target cell size. Before version 2.0.5 this '
      + 'layer would have been silently ignored. It is included here '
      + 'deliberately, to exercise the fix.'),
    H.spacer(),

    H.h2('5.1  Step 1 — Set the coordinate system'),
    H.stepR([['Click ', ''], ['Set / change CRS…', 'b'], [' in the Coordinate system panel.', '']]),
    H.stepR([['Type ', ''], ['32631', 'c'], [' — an EPSG code is enough; a full PROJ or WKT string also works.', '']]),
    H.step('The dialog validates as you type and names the system it resolved, so you can confirm before committing.'),
    H.stepR([['Click ', ''], ['OK', 'b'], ['.', '']]),
    ...H.figure('03_dialog_crs', 330, 'Setting the project coordinate system to EPSG:32631.'),
    H.p('The panel now reads "WGS 84 / UTM zone 31N (EPSG:32631) — unit: '
      + 'meter". Every cell size you type from here on is in metres.'),
    ...H.figure('04_panel_crs_set', 430, 'The CRS panel once the coordinate system is set.'),
    H.note('Shortcut.', 'You can skip this step. Importing the limit polygon '
      + 'first adopts the CRS from its .prj file automatically — the tutorial '
      + 'sets it explicitly only to show the dialog.'),
    H.spacer(),

    H.h2('5.2  Step 2 — Import the model limit'),
    H.stepR([['Choose ', ''], ['File → Import limit polygon…', 'b'], ['.', '']]),
    H.stepR([['Select ', ''], ['Example\\modelLimit.shp', 'c'], ['.', '']]),
    H.spacer(60),
    H.p('The boundary appears in cyan and the map zooms to it. The Log records '
      + 'the import and the CRS it detected.'),
    ...H.figure('05_limit_imported', H.PX, 'The model limit loaded and fitted to the window.'),
    H.note('If the limit will not load.', 'It must be exactly one single-part '
      + 'polygon. A multipart feature, or a file with several polygons, will be '
      + 'reduced to its largest part — dissolve or clip it in GIS first if that '
      + 'is not what you want.'),
    H.spacer(),

    H.h2('5.3  Step 3 — Add the refinement layers'),
    H.p('Repeat this for each of the five layers:'),
    H.stepR([['Choose ', ''], ['File → Import refinement shapefile…', 'b'], ['.', '']]),
    H.step('Pick the shapefile.'),
    H.step('Give the layer a name and its target cell size, then click OK.'),
    ...H.figure('06_dialog_refinement_size', 320,
      'The refinement dialog. The cell-size unit follows the project CRS — metres here.'),
    H.p('Import the five layers with these sizes. They step down from the '
      + 'boundary to the wells, so cells coarsen smoothly outwards:'),
    H.table(
      ['Order', 'Shapefile', 'Layer name', 'Geometry', 'Target cell size'],
      [
        ['1', [['modelGhb.shp', 'c']], 'modelGhb', 'Line (2 features)', '10 m'],
        ['2', [['site.shp', 'c']], 'site', 'Polygon (1 feature)', '4 m'],
        ['3', [['hfb.shp', 'c']], 'hfb', 'Line (1 feature)', '3 m'],
        ['4', [['drains.shp', 'c']], 'drains', 'Line (2 features)', '2 m'],
        ['5', [['pointWell.shp', 'c']], 'pointWell', 'Point (2 features)', '1 m'],
      ],
      [900, 2400, 2000, 2700, 2080]),
    H.spacer(120),
    H.p('Each layer is drawn in its own colour, and the panel lists them in import order.'),
    ...H.figure('07_layers_loaded', H.PX,
      'All five refinement layers loaded. The red general-head boundary follows '
      + 'the model edge; the site, barrier, drains and wells cluster in the middle.'),
    ...H.figure('08_panel_layers', 430, 'The refinement layers panel after all five imports.'),
    H.spacer(),

    H.h2('5.4  Step 4 — Set the refinement options'),
    H.p('Scroll the sidebar to "Voronoi refinement options" and enter:'),
    H.table(
      ['Option', 'Value', 'Why'],
      [
        ['Coarse (max) cell size', '20 m', 'About 1/15 of the model’s 291 m short side — coarse in the empty corners, still enough cells to resolve the domain.'],
        ['Refinement multiplier', '1.3', 'A gentle 30 % growth per ring, so the step from 1 m at the wells to 20 m at the edges is smooth.'],
        ['Allow overlapping refinement', 'On', 'The site, barrier, drains and wells all sit on top of one another.'],
        ['Fix short edges below', '0.2 m', 'A fifth of the finest target size (1 m). See the caution in section 5.7 before changing it.'],
      ],
      [2900, 1300, 5880]),
    H.spacer(120),
    ...H.figure('10_panel_options', 430, 'The refinement options set for this tutorial.'),
    H.spacer(),

    H.h2('5.5  Step 5 — Generate the mesh'),
    H.stepR([['Click ', ''], ['⚙  Generate Voronoi mesh', 'b'],
      [' in the Mesh panel, or the gear button on the toolbar.', '']]),
    H.step('Give the mesh a name — it becomes the prefix for exported files. The default is voronoiModel.'),
    ...H.figure('16_dialog_mesh_name', 260, 'Naming the mesh before generation.'),
    H.p('Meshing runs in the background and the Log fills in as it goes. This '
      + 'example completed in about three seconds. When it finishes you get an '
      + 'in-app popup and a Windows notification, so you can leave the window '
      + 'in the background.'),
    ...H.figure('23_popup_mesh_done', 380,
      'The completion popup, which repeats the headline quality figures.'),
    ...H.figure('17_mesh_generated', H.PX,
      'The finished mesh: 1,134 cells, fine at the centre and coarse towards the corners.'),
    H.spacer(),

    H.h2('5.6  Step 6 — Inspect the mesh'),
    H.p('Zoom in on the middle of the model to see the refinement actually '
      + 'working. Use the mouse wheel, the toolbar zoom buttons, or View → Zoom '
      + 'to data to get back out.'),
    ...H.figure('22_canvas_zoom_site', 600,
      'Progressive refinement around the site: 20 m cells at the top, '
      + 'tightening through the site footprint to 1 m cells at the two wells '
      + '(magenta). The barrier is blue and the drains orange.'),
    H.p('This is the check worth making every time: the cells should tighten '
      + 'smoothly towards each feature, with no abrupt jump from coarse to '
      + 'fine. An abrupt jump means the multiplier is too high for the range of '
      + 'cell sizes you asked for.'),
    H.spacer(),

    H.h2('5.7  Step 7 — Read the quality report'),
    H.p('The report fills in automatically. These are the actual numbers from this run:'),
    H.table(
      ['Metric', 'Value', 'Reading it'],
      [
        ['Cells (ncpl)', '1,134', 'A comfortable size for a site model.'],
        ['Vertices (nvert)', '0 → 2,527', 'Shows 0 until the DISV properties are computed; after a DISV or ModelMuse export it reports 2,527.'],
        ['Cell area min', '0.00 m²', 'Slivers left where the tessellation was clipped to the boundary. Only three cells are under 0.01 m², and all three sit on the edge.'],
        ['Cell area max', '400.00 m²', 'Exactly the 20 m coarse size squared — the coarse setting was reached.'],
        ['Cell area mean / median', '39.06 / 3.60 m²', 'The gap between them is the refinement doing its job: most cells are small, a few are coarse.'],
        ['Total area', '44,293.75 m²', 'Identical to the model limit polygon’s area — the clip is exact.'],
        ['Vertices per cell', '3 / 29 / 6.10', 'A mean near six is healthy for a Voronoi grid.'],
        ['Shortest edge', '0.0066 m', 'The shortest edge anywhere in the mesh.'],
        ['Mean of min edges', '1.2749 m', 'Typical cells are far from degenerate.'],
        ['Cells with short edges', '220', 'Cells with an edge below the 0.2 m threshold — see the caution below.'],
      ],
      [2500, 1900, 5680]),
    H.spacer(140),
    H.note('Reading "Cells with short edges" correctly.',
      'This count is relative to the threshold you set, so it is easy to '
      + 'misread. Set it to 0.5 m on this same mesh and 60 % of cells are '
      + 'flagged; at 0.2 m, 19 % are. That is arithmetic, not a defect — a '
      + 'Voronoi tessellation with 1 m target cells naturally has many edges '
      + 'shorter than half a metre. Set the threshold to a small fraction of '
      + 'your finest target cell size, and treat the number as a trend to watch '
      + 'between runs rather than an absolute pass or fail.'),
    H.spacer(120),
    H.p('The Log records the boundary clip explicitly:'),
    ...H.figure('20_panel_log', 430,
      'The Log confirming the clip and the final cell count. "20 sliver/empty '
      + 'cell(s) removed" is the 2.0.5 boundary workaround tidying up after itself.'),
    H.rp([['Save the report with ', ''], ['Save report…', 'b'], [' or ', ''],
      ['File → Export quality report…', 'b'],
      [', as CSV or JSON — worth keeping alongside the model as a record of the '
       + 'grid you built.', '']]),
    H.spacer(),

    H.h2('5.8  Step 8 — Export the mesh and the DISV properties'),
    H.table(
      ['Command', 'Produces', 'Use it for'],
      [
        ['File → Export mesh shapefile…',
          [['voronoiModel_voronoi.shp', 'c'], [' plus .shx, .dbf, .prj, .cpg', '']],
          'Viewing or post-processing the grid in QGIS or ArcGIS'],
        ['File → Export DISV properties (JSON)…',
          [['voronoiModel_disv.json', 'c']],
          'Scripting with FloPy, or feeding another tool the raw DISV arrays'],
        ['File → Export quality report…',
          [['voronoiModel_report.csv', 'c'], [' or .json', '']],
          'Documenting the grid'],
      ],
      [3300, 3300, 3480]),
    H.spacer(120),
    H.rp([['The DISV JSON for this mesh holds ', ''], ['ncpl', 'c'], [' 1,134, ', ''],
      ['nvert', 'c'], [' 2,527, and the ', ''], ['vertices', 'c'], [', ', ''],
      ['cell2d', 'c'], [' and ', ''], ['centroids', 'c'],
      [' arrays MODFLOW 6 needs to describe an unstructured grid.', '']]),
    H.spacer(),

    H.h2('5.9  Step 9 — Export a ModelMuse MODFLOW 6 model'),
    H.p('This is the step that turns a grid into a model. The application '
      + 'writes a complete MODFLOW 6 DISV simulation with FloPy, sampling your '
      + 'elevation rasters at every cell centroid.'),
    H.h3('Optional: attach rasters to a layer first'),
    H.p('Select a refinement layer and click "Layer top/botm rasters…" to '
      + 'attach a top and a bottom raster. These pre-fill the export dialog, so '
      + 'you do not have to browse for them again.'),
    ...H.figure('24_dialog_layer_rasters', 380, 'Attaching elevation rasters to a refinement layer.'),
    H.h3('The export dialog'),
    H.stepR([['Choose ', ''], ['File → Export ModelMuse MODFLOW 6 model…', 'b'], ['.', '']]),
    H.step('Set the number of layers to 4.'),
    H.stepR([['For the model top, click ', ''], ['Raster…', 'b'], [' and choose ', ''],
      ['modelTop.tif', 'c'], ['.', '']]),
    H.stepR([['For each layer bottom, choose ', ''], ['bottomLy1.tif', 'c'], [' through ', ''],
      ['bottomLy4.tif', 'c'], ['.', '']]),
    H.step('Choose an empty output folder and click OK.'),
    ...H.figure('25_dialog_modelmuse', 400,
      'The ModelMuse export dialog, configured for four layers with a raster '
      + 'for the top and for every layer bottom.'),
    H.note('Constants or rasters.', 'Every surface accepts either. Type a '
      + 'number for a flat surface, or point at a GeoTIFF to have it sampled at '
      + 'each cell centroid. You can mix the two — a raster top over flat layer '
      + 'bottoms is a common setup.'),
    H.spacer(120),
    H.h3('What you get'),
    H.p('The export writes eight files. These are the actual outputs from this tutorial run:'),
    H.table(
      ['File', 'Size', 'Contents'],
      [
        [[['mfsim.nam', 'c']], '345 B', 'Simulation name file — the one you point ModelMuse at'],
        [[['voronoiModel.disv', 'c']], '291 KB', 'The unstructured grid: NLAY 4, NCPL 1,134, NVERT 2,527, plus top and botm'],
        [[['voronoiModel.nam', 'c']], '266 B', 'Groundwater-flow model name file'],
        [[['voronoiModel.tdis', 'c']], '221 B', 'Time discretisation'],
        [[['voronoiModel.ims', 'c']], '123 B', 'Iterative solver settings'],
        [[['voronoiModel.npf', 'c']], '211 B', 'Node-property flow package'],
        [[['voronoiModel.ic', 'c']], '77 KB', 'Initial conditions'],
        [[['voronoiModel.oc', 'c']], '245 B', 'Output control'],
      ],
      [2700, 1200, 6180]),
    H.spacer(120),
    H.ok('Verified.', 'In this run the four layer bottoms came out of the '
      + 'rasters as −4.0, −7.5, −20.0 and −50.0 m, and the top as 0.0 m — '
      + 'matching the source GeoTIFFs exactly, so the centroid sampling is '
      + 'doing what it claims.'),
    H.spacer(120),
    H.h3('Importing into ModelMuse'),
    H.stepR([['In ModelMuse choose ', ''],
      ['File → Import → Import MODFLOW-6 Model…', 'b'], ['.', '']]),
    H.stepR([['Select the ', ''], ['mfsim.nam', 'c'], [' file the export wrote.', '']]),
    H.step('ModelMuse reads the DISV grid, the layer elevations and the packages, and you can carry on building the model there.'),
    H.spacer(),

    H.h2('5.10  Step 10 — Save the project'),
    H.rp([['Use ', ''], ['File → Save project', 'b'], [' (', ''], ['Ctrl+S', 'c'],
      [') to write everything — CRS, limit, refinement layers, voids, '
       + 'background images, options and the generated mesh — into a single ', ''],
      ['.mf6vor', 'c'],
      [' file. The tutorial project came to about 807 KB, the mesh being most of it.', '']]),
    H.p('The window title shows the current file name and an asterisk while '
      + 'there are unsaved changes. Closing the application, starting a new '
      + 'project or opening another one asks whether to save first.'),
    ...H.figure('28_main_final', H.PX, 'The completed tutorial project, meshed and reported.'),
    H.pageBreak(),

    /* =============================================== 6. Own data == */
    H.h1('6. Working with your own data'),

    H.h2('6.1  Drawing instead of importing'),
    H.p('Anything you can import you can also draw. Use it to sketch a boundary '
      + 'before the GIS data exists, or to add a refinement zone around '
      + 'something you noticed on a background image.'),
    H.stepR([['Choose the mode from the ', ''], ['Draw', 'b'],
      [' menu or the toolbar. For a refinement layer you are asked for a name '
       + 'and cell size first.', '']]),
    H.step('Click on the map to place vertices. Each finished feature appears immediately, and an on-canvas counter tracks how many you have drawn.'),
    H.step('Double-click or press Enter to finish the current shape. In point mode each click is a complete feature on its own.'),
    H.step('Keep going to add more features to the same layer, then choose "Finish current layer" (the check button) to commit it.'),
    H.step('"Cancel current layer" (the bin button) discards everything drawn in this session.'),
    H.spacer(80),
    H.note('Remember to finish the layer.', 'Features you have drawn are not '
      + 'part of the project until you finish the layer. If mesh generation '
      + 'ignores something you just drew, check that you clicked the check button.'),
    H.spacer(),

    H.h2('6.2  Void polygons'),
    H.p('Draw one with Draw → New void polygon…, or import a shapefile of them '
      + 'with File → Import void polygon shapefile…. Cells inside a void are '
      + 'removed, and cells straddling its edge are clipped to it.'),
    H.p('Voids must sit inside the model limit. Because a DISV cell cannot have '
      + 'a hole, a void that would perforate a single large cell removes that '
      + 'cell instead of punching through it — so keep your coarse cell size '
      + 'smaller than the voids you need to represent.'),

    H.h2('6.3  Background images'),

    H.h3('6.3.1  From a local file'),
    H.p('The "From file" tab accepts a GeoTIFF, or a PNG/JPG with a world '
      + 'file. Without either, you are asked for the extent directly:'),
    ...H.figure('26_dialog_image_extent', 340,
      'Entering an image extent by hand, in project coordinates.'),
    H.p('Get the extent wrong and the image lands in the wrong place; correct '
      + 'it by removing the image and re-importing it.'),

    H.h3('6.3.2  Online satellite imagery'),
    H.p('The "Online satellite map" tab fetches free basemap imagery directly '
      + 'from the internet, so you do not need to source and georeference a '
      + 'file yourself:'),
    H.step('Choose a provider — Esri World Imagery (satellite) or Sentinel-2 '
      + 'Cloudless (EOX). Both are free and need no account or API key.'),
    H.step('Find the area you need: type a place name into Search, click "Fit '
      + 'to project extent" to jump straight to your model’s location, or pan '
      + '(drag) and zoom (mouse wheel / the +/− buttons) manually.'),
    H.step('Optionally click "Draw export area" and drag a rectangle over the '
      + 'exact region you want. Without one, the current view is used.'),
    H.step('Click "Export GeoTIFF…" to save the image to a file for later, or '
      + '"Add to project as background…" to save it and add it immediately.'),
    ...H.figure('30_dialog_online_imagery', H.PX,
      'The online satellite map, fitted to the tutorial project’s extent. '
      + 'The info line below the map reports the source, zoom level, ground '
      + 'resolution and tile count before you download anything.'),
    H.p('The downloaded tiles are stitched together and reprojected from Web '
      + 'Mercator into the project’s coordinate system, then written as a '
      + 'GeoTIFF with an embedded CRS — the same kind of file the "From file" '
      + 'tab reads, so it can be re-imported anywhere later.'),
    H.note('No project CRS yet?', 'If the project has no coordinate system '
      + 'set, the image is reprojected into an automatically detected UTM '
      + 'zone instead, and you are asked whether to adopt that zone as the '
      + 'project CRS.'),
    H.note('Area too large.', 'A live tile-count estimate warns you before '
      + 'downloading if the selected area would need too many tiles at the '
      + 'current zoom level. Zoom in, or draw a smaller area, to proceed.'),
    H.note('Licensing.', 'Both providers are free for personal and evaluation '
      + 'use; check their terms before using exported imagery commercially or '
      + 'redistributing it.'),

    H.h2('6.4  Measuring distances'),
    H.p('View → Measure distance (or the ruler button) turns the cursor into a '
      + 'measure tool. Click a start point, then an end point, and the distance '
      + 'is reported in the project’s length unit. Click again to start a new '
      + 'measurement; Esc cancels one in progress. It is the quickest way to '
      + 'sanity-check a candidate cell size against a real feature before you '
      + 'type it in.'),

    H.h2('6.5  Choosing refinement sizes'),
    H.bulletR([['Work from the finest feature outwards. ', 'b'],
      ['Decide what the smallest cell has to be — usually set by a well or a '
       + 'narrow feature — then let the multiplier carry it out to the coarse size.']]),
    H.bulletR([['Keep the range sane. ', 'b'],
      ['The tutorial spans 1 m to 20 m, a factor of 20. Much beyond a factor of '
       + '50 and you should expect either a very large grid or visible jumps in '
       + 'cell size.']]),
    H.bulletR([['Order the layers coarse to fine. ', 'b'],
      ['Boundaries at the coarsest refinement, then areas, then lines, then '
       + 'points. That is the order used in Chapter 5.']]),
    H.bulletR([['Watch the cell count. ', 'b'],
      ['Halving a target cell size roughly quadruples the cells in that zone. '
       + 'Generate, read the report, adjust, generate again — a run on a model '
       + 'this size takes seconds.']]),
    H.bulletR([['Check the total area every time. ', 'b'],
      ['It should equal your model limit area. If it does not, the clip lost '
       + 'cells and something is wrong with the limit polygon.']]),
    H.pageBreak(),

    /* ========================================== 7. Troubleshooting == */
    H.h1('7. Troubleshooting'),
    H.table(
      ['Symptom', 'Cause', 'What to do'],
      [
        ['"Set or import a CRS first" when importing a refinement layer',
          'No coordinate system yet.',
          'Set it in the CRS panel, or import the limit polygon first so its .prj is adopted.'],
        ['"This shapefile’s CRS differs from the project CRS"',
          'Mixed coordinate systems.',
          'Re-project the file in GIS to the project CRS. The application will not re-project for you.'],
        ['A warning that a shapefile has no .prj',
          'No coordinate system information alongside the file.',
          'The file is assumed to be in the project CRS already. Confirm that it is, or features will be misaligned.'],
        ['A refinement layer seems to have no effect',
          'Before 2.0.5, a layer running closer to the boundary than its own cell size was silently dropped.',
          'Confirm with Help → About that you are on 2.0.5 or later. If you are, check the layer is actually inside the limit and its cell size is smaller than the coarse size.'],
        ['The limit will not import',
          'It is multipart, or the file holds several polygons.',
          'Dissolve or clip it to exactly one single-part polygon.'],
        ['Far more cells than expected, or a very slow run',
          'The finest target size is very small relative to the coarse size, or the multiplier is low.',
          'Raise the finest target size, or raise the multiplier towards 1.5, and regenerate.'],
        ['"Cells with short edges" is alarmingly high',
          'The threshold is large relative to your finest target cell size.',
          'Set it to a small fraction of the finest target size — see section 5.7. Check "Shortest edge" and "Mean of min edges" too.'],
        ['Total area is less than the model limit area',
          'Cells were lost during clipping.',
          'Check the limit polygon is valid and not self-intersecting; check the Log for how many slivers were removed.'],
        ['Vertices (nvert) shows 0',
          'The DISV properties have not been computed yet.',
          'Expected. Export the DISV JSON or the ModelMuse model, then recompute the report.'],
        ['No mesh-finished notification',
          'Windows can suppress toasts from unsigned applications; Focus Assist blocks them too.',
          'The in-app popup always appears regardless — 2.0.4 added it for exactly this reason.'],
        ['Drawn features vanish',
          'The layer was never finished.',
          'Click the check button (Finish current layer) to commit what you have drawn.'],
        ['Mesh generation fails',
          'Various.',
          'Read the Log panel — it carries the full traceback and the mf6Voronoi messages.'],
      ],
      [2800, 3200, 4080]),
    H.pageBreak(),

    /* ================================================ Appendices == */
    H.h1('Appendix A. Tutorial run at a glance'),
    H.p('Reference values from the run this manual documents. Your numbers will '
      + 'match if you follow Chapter 5 exactly.'),
    H.table(
      ['Item', 'Value'],
      [
        ['Application version', '3.0.0'],
        ['Coordinate system', 'WGS 84 / UTM zone 31N (EPSG:32631), unit metre'],
        ['Model limit extent', '592,707.1 – 593,008.9 E; 5,762,469.6 – 5,762,760.0 N'],
        ['Model limit size', '301.8 m × 290.5 m, area 44,293.7 m²'],
        ['Refinement layers', 'modelGhb 10 m, site 4 m, hfb 3 m, drains 2 m, pointWell 1 m'],
        ['Coarse (max) cell size', '20 m'],
        ['Refinement multiplier', '1.3'],
        ['Allow overlapping refinement', 'On'],
        ['Fix short edges below', '0.2 m'],
        ['Cells generated (ncpl)', '1,134'],
        ['Vertices (nvert)', '2,527'],
        ['Generation time', 'about 3 seconds'],
        ['Cell area (min / median / mean / max)', '0.00 / 3.60 / 39.06 / 400.00 m²'],
        ['Total mesh area', '44,293.75 m² — equal to the limit polygon area'],
        ['Vertices per cell (min / mean / max)', '3 / 6.10 / 29'],
        ['Shortest edge / mean of min edges', '0.0066 m / 1.2749 m'],
        ['Cells with an edge below 0.2 m', '220 of 1,134 (19 %)'],
        ['Sliver cells removed by the boundary clip', '20'],
        ['ModelMuse export', '4 layers; top 0 m; bottoms −4, −7.5, −20, −50 m'],
        ['Project file size', 'about 807 KB'],
      ],
      [4000, 6080]),
    H.spacer(200),

    H.h1('Appendix B. Output files'),
    H.table(
      ['Format', 'Written by', 'What it is'],
      [
        [[['.mf6vor', 'c']], 'File → Save project',
          'The whole session — CRS, limit, layers, voids, background images, options and the generated mesh'],
        [[['.shp', 'c'], [' set', '']], 'File → Export mesh shapefile…',
          'The Voronoi cells as an ESRI polygon shapefile with a .prj'],
        [[['.json', 'c'], [' (DISV)', '']], 'File → Export DISV properties…',
          'ncpl, nvert, vertices, cell2d, centroids and uniqueVerticesList'],
        [[['.csv', 'c'], [' / ', ''], ['.json', 'c']], 'File → Export quality report…',
          'Every metric in the quality report'],
        ['MODFLOW 6 model folder', 'File → Export ModelMuse MODFLOW 6 model…',
          'mfsim.nam plus the .disv, .nam, .tdis, .ims, .npf, .ic and .oc files'],
      ],
      [2400, 3400, 4280]),
    H.spacer(200),

    H.h1('Appendix C. Credits and further reading'),
    H.p('mf6Voronoi Studio is a graphical front-end for the mf6Voronoi package '
      + 'by Hatari Labs, available at https://github.com/hatarilabs/mf6Voronoi.'),
    H.bullet('mf6Voronoi — Saul Montoya'),
    H.bullet('GUI developer — An Ho Taylor'),
    H.spacer(80),
    H.p('Viva el Software Libre', { run: { italics: true, color: '5A6672' } }),
  ],
};
