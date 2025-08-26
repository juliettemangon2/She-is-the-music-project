<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Song Metadata Explorer</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  /* Base */
  body {
    font-family: 'Inter', sans-serif;
    margin: 0;
    display: flex;
    height: 100vh;
    background: #fafafa;
    color: #111827;
  }

  /* Sidebar */
  .sidebar {
    width: 220px;
    background: #ffffff;
    border-right: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
    padding: 1.5rem 0;
  }
  .sidebar h1 {
    font-size: 1.4rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 2rem;
    color: #111827;
  }
  .nav-link {
    display: block;
    padding: 0.75rem 1rem;
    font-size: 1rem;
    font-weight: 500;
    color: #374151;
    margin: 0.25rem 0.75rem;
    border-radius: 0.5rem;
    transition: background 0.2s ease, color 0.2s ease;
  }
  .nav-link:hover {
    background: #f3f4f6;
    color: #2563eb;
  }
  .nav-link.active {
    background: #e0f2fe;
    color: #1d4ed8;
    font-weight: 600;
  }

  /* Main */
  .main {
    flex: 1;
    background: #ffffff;
    padding: 2rem;
    overflow-y: auto;
  }
  .section h2 {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 1rem;
    color: #111827;
  }

  /* Cards */
  .song-card, .database-card {
    background: #fff;
    border-radius: 1rem;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    border: 1px solid #f3f4f6;
    transition: transform 0.2s ease;
  }
  .song-card:hover, .database-card:hover {
    transform: translateY(-3px);
  }

  /* Buttons */
  button {
    font-size: 0.95rem;
    font-weight: 600;
    border-radius: 0.5rem;
    padding: 0.5rem 1rem;
    transition: background 0.2s ease;
  }
  #addSongBtn {
    background: #fce7f3;
    color: #9d174d;
  }
  #addSongBtn:hover {
    background: #fbcfe8;
  }
  #submitBtn {
    background: #2563eb;
    color: #fff;
  }
  #submitBtn:hover {
    background: #1d4ed8;
  }
  .bg-gray-200 {
    background: #f3f4f6 !important;
  }
  .bg-gray-200:hover {
    background: #e5e7eb !important;
  }

  /* Inputs */
  input[type="text"] {
    border: 1px solid #d1d5db;
    border-radius: 0.5rem;
    padding: 0.5rem 0.75rem;
    font-size: 0.95rem;
    width: 100%;
    transition: border-color 0.2s ease;
  }
  input[type="text"]:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 1px #2563eb;
  }

  /* Insights Panel */
  #insights, #database-insights {
    background: #f9fafb;
    border-radius: 1rem;
    padding: 1.5rem;
    margin-top: 1rem;
    border: 1px solid #e5e7eb;
  }
  #insights h3, #database-insights h3 {
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
  }

  /* Functional classes */
  .card-content {
    transition: max-height 0.4s ease, opacity 0.4s ease;
    overflow: hidden;
    max-height: 1000px;
  }
  .collapsed {
    max-height: 0 !important;
    opacity: 0;
    padding: 0 !important;
  }
  .expanded {
    opacity: 1;
  }
  .highlight {
    border: 3px solid #f59e0b;
    box-shadow: 0 0 8px #fbbf24;
  }
  .insight-item {
    display: inline-block;
    margin: 4px;
    padding: 6px 10px;
    background: #f1f5f9;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    transition: background 0.2s ease;
  }
  .insight-item:hover {
    background: #e2e8f0;
  }

  /* Graph */
  #network {
    border-radius: 0.75rem;
    background: #fff;
    border: 1px solid #f3f4f6;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
  }
  #graph-controls {
    border-radius: 0.75rem;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
  }

  /* Toggle buttons */
  .toggle-card {
    background: #f3f4f6;
    font-size: 0.75rem;
    border-radius: 0.5rem;
  }
  .toggle-card:hover {
    background: #e5e7eb;
  }
</style>
</head>
<body class="flex h-screen bg-gray-100 text-gray-800 font-sans">

<!-- Sidebar -->
<div class="w-64 bg-blue-100 flex flex-col">
  <h1 class="text-xl font-bold text-center text-blue-900 py-6 border-b border-blue-200">Music Data Tool</h1>
  <nav class="flex flex-col mt-4">
    <a href="#" class="nav-link px-6 py-4 hover:bg-blue-200" data-section="song-input">Song Input</a>
    <a href="#" class="nav-link px-6 py-4 hover:bg-blue-200" data-section="graph">Graph</a>
    <a href="#" class="nav-link px-6 py-4 hover:bg-blue-200" data-section="database">Database</a>
  </nav>
</div>

<!-- Main Content -->
<div class="flex-1 p-6 overflow-y-auto bg-white">

  <!-- Song Input -->
  <div id="song-input" class="section">
    <h2 class="text-2xl font-bold mb-6">Song Input</h2>
    <form id="songForm" class="space-y-4">
      <div id="songInputs" class="space-y-3">
        <div class="bg-gray-50 p-4 rounded flex gap-4 items-center">
          <input type="text" name="artist" placeholder="Artist Name" required class="border rounded px-4 py-2 flex-1">
          <input type="text" name="title" placeholder="Song Title" required class="border rounded px-4 py-2 flex-1">
        </div>
      </div>
      <div class="flex gap-4">
        <button type="button" id="addSongBtn" class="bg-pink-100 text-blue-900 font-medium px-4 py-2 rounded hover:bg-pink-200">+ Add Song</button>
        <button type="submit" id="submitBtn" class="bg-blue-500 text-white font-semibold px-4 py-2 rounded hover:bg-blue-600">Submit</button>
      </div>
    </form>
    <div class="mt-8">
      <div class="flex justify-end gap-4 mb-4 hidden" id="toggleControlsSongInput">
        <button id="expandAllInput" class="bg-gray-200 px-3 py-2 rounded hover:bg-gray-300">Expand All</button>
        <button id="collapseAllInput" class="bg-gray-200 px-3 py-2 rounded hover:bg-gray-300">Collapse All</button>
      </div>
      <div id="results"></div>
      <div id="insights" class="mt-6"></div>
    </div>
  </div>

  <!-- Graph -->
  <div id="graph" class="section hidden">
    <h2 class="text-2xl font-bold mb-4">Graph Visualization</h2>
    <div class="space-y-3 mb-4">
      <div class="flex flex-wrap items-center gap-4">
        <button id="graphCurrentBtn" class="bg-blue-500 text-white font-semibold px-4 py-2 rounded hover:bg-blue-600">Graph Current Input</button>
        <button id="graphDatabaseBtn" class="bg-gray-200 text-gray-800 font-semibold px-4 py-2 rounded hover:bg-gray-300">Graph Database</button>
        <button id="resetFilters" class="bg-gray-300 px-3 py-2 rounded hover:bg-gray-400">Reset Filters</button>
      </div>
      <div class="flex flex-wrap items-center gap-4">
        <label><input type="checkbox" class="filter-toggle" value="contributor" checked> Contributors</label>
        <label><input type="checkbox" class="filter-toggle" value="label" checked> Labels</label>
        <label><input type="checkbox" class="filter-toggle" value="publisher" checked> Publishers</label>
        <label><input type="checkbox" class="filter-toggle" value="genre" checked> Genres</label>
        <div class="flex items-center gap-2">
          <span>Track Pop:</span>
          <input type="range" id="trackPopularity" min="0" max="100" value="0" class="w-24">
          <span id="trackPopularityVal">0+</span>
        </div>
        <div class="flex items-center gap-2">
          <span>Artist Pop:</span>
          <input type="range" id="artistPopularity" min="0" max="100" value="0" class="w-24">
          <span id="artistPopularityVal">0+</span>
        </div>
      </div>
    </div>
    <div class="flex gap-6 h-[600px]">
      <div id="network" class="flex-1 border rounded shadow bg-white"></div>
      <div id="graph-controls" class="w-72 bg-gray-50 border rounded p-4 space-y-4 overflow-y-auto">
        <h3 class="font-semibold mb-2">Legend</h3>
        <div class="text-sm space-y-1">
          <div><span class="inline-block w-3 h-3 rounded-full bg-blue-300 mr-2"></span>Song</div>
          <div><span class="inline-block w-3 h-3 rounded-full bg-yellow-400 mr-2"></span>Contributor</div>
          <div><span class="inline-block w-3 h-3 rounded-full bg-orange-500 mr-2"></span>Label</div>
          <div><span class="inline-block w-3 h-3 rounded-full bg-pink-500 mr-2"></span>Publisher</div>
          <div><span class="inline-block w-3 h-3 rounded-full bg-teal-500 mr-2"></span>Genre</div>
        </div>
        <h3 class="font-semibold mb-2 mt-4">Node Details</h3>
        <div id="details-panel" class="text-sm p-2 bg-white border rounded">Select a node to view details.</div>
      </div>
    </div>
  </div>

  <!-- Database -->
  <div id="database" class="section hidden">
    <h2 class="text-2xl font-bold mb-4">Database</h2>
    <div class="flex justify-end gap-4 mb-4">
      <button id="expandAllDB" class="bg-gray-200 px-3 py-2 rounded hover:bg-gray-300">Expand All</button>
      <button id="collapseAllDB" class="bg-gray-200 px-3 py-2 rounded hover:bg-gray-300">Collapse All</button>
    </div>
    <div id="database-results" class="space-y-4"></div>
    <div id="database-insights" class="mt-6"></div>
    <div class="mt-4">
      <button id="databaseGraphBtn" class="bg-blue-500 text-white font-semibold px-4 py-2 rounded hover:bg-blue-600">Graph All Database Songs</button>
    </div>
  </div>
</div>

<script>
let currentData = null, databaseData = null, latestData = null, network = null;
const colors = { song: '#8ecae6', contributor: '#ffb703', label: '#fb8500', publisher: '#ff006e', genre: '#219ebc' };

// Navigation
document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('bg-blue-200', 'font-semibold'));
    link.classList.add('bg-blue-200', 'font-semibold');
    document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
    document.getElementById(link.dataset.section).classList.remove('hidden');
    if (link.dataset.section === 'database') loadDatabase();
  });
});

document.getElementById('addSongBtn').addEventListener('click', () => {
  const div = document.createElement('div');
  div.classList.add('bg-gray-50', 'p-4', 'rounded', 'flex', 'gap-4', 'items-center');
  div.innerHTML = '<input type="text" name="artist" placeholder="Artist Name" class="border rounded px-4 py-2 flex-1"><input type="text" name="title" placeholder="Song Title" class="border rounded px-4 py-2 flex-1"><button type="button" class="remove-song bg-red-100 text-red-600 px-3 py-1 rounded hover:bg-red-200">Remove</button>';
  document.getElementById('songInputs').appendChild(div);
  updateSubmitButtonText();
  div.querySelector('.remove-song').addEventListener('click', () => { div.remove(); updateSubmitButtonText(); });
});

function updateSubmitButtonText() {
  const count = document.querySelectorAll('input[name="artist"]').length;
  document.getElementById('submitBtn').textContent = (count > 1) ? "Compare Songs" : "Submit";
}

// Submit Songs
document.getElementById('songForm').addEventListener('submit', async e => {
  e.preventDefault();
  let query = '/api/songdata?', artists = document.querySelectorAll('input[name="artist"]'), titles = document.querySelectorAll('input[name="title"]');
  artists.forEach((a, i) => query += `artist=${encodeURIComponent(a.value)}&title=${encodeURIComponent(titles[i].value)}&`);
  const res = await fetch(query);
  const data = await res.json();
  currentData = data;
  latestData = { songs: data.songs, graph: buildGraphFromSongs(data.songs) };
  displayResults('results', data.songs, 'toggleControlsSongInput');
  if (data.songs.length > 1) displayInsights(data.derived_insights, 'insights'); else document.getElementById('insights').innerHTML = '';
});

// Expand/Collapse All
document.getElementById('expandAllInput').addEventListener('click', () => toggleAll('results', true));
document.getElementById('collapseAllInput').addEventListener('click', () => toggleAll('results', false));
document.getElementById('expandAllDB').addEventListener('click', () => toggleAll('database-results', true));
document.getElementById('collapseAllDB').addEventListener('click', () => toggleAll('database-results', false));

function toggleAll(containerId, expand) {
  document.querySelectorAll(`#${containerId} .card-content`).forEach(c => {
    c.classList.toggle('collapsed', !expand);
    c.classList.toggle('expanded', expand);
    const btn = c.parentElement.querySelector('.toggle-card');
    btn.textContent = expand ? 'Collapse' : 'Expand';
  });
}

// Load Database
async function loadDatabase() {
  const res = await fetch('/api/database');
  const data = await res.json();
  if (data.songs) {
    databaseData = data.songs;
    displayResults('database-results', databaseData);
    if (data.derived_insights) displayInsights(data.derived_insights, 'database-insights');
    latestData = { songs: databaseData, graph: buildGraphFromSongs(databaseData) };
  }
}

// Display Songs
function displayResults(containerId, songs, controlsId = null) {
  const container = document.getElementById(containerId);

  // Debug: confirm function is triggered and data is valid
  console.log(`displayResults() called for #${containerId}, songs count:`, songs.length);

  // Clear old content
  container.innerHTML = '';

  // If no songs, show fallback message
  if (!songs || songs.length === 0) {
    container.innerHTML = '<p class="text-gray-500">No songs available.</p>';
    return;
  }

  // ✅ Make sure container is visible (in case CSS keeps it hidden)
  container.classList.remove('hidden');

  // Create grid wrapper for cards
  const grid = document.createElement('div');
  grid.className = 'grid gap-6 md:grid-cols-2 lg:grid-cols-3';

  // Render each song card
  songs.forEach(song => {
    const safe = (val) => val ? val : '';

    const contributorsHTML = (song.contributors || []).map(c =>
      `<li><span class="font-semibold">${c.name}</span> ${(c.roles || []).map(r => `<span class="bg-yellow-100 text-yellow-800 text-xs px-2 py-0.5 rounded">${r}</span>`).join(' ')}</li>`
    ).join('');

    const genresHTML = (song.genres || []).map(g =>
      `<span class="bg-teal-100 text-teal-800 text-xs px-2 py-0.5 rounded">${g}</span>`
    ).join('');

    const publishersHTML = (song.publishers || []).map(p =>
      `<span class="bg-pink-100 text-pink-800 text-xs px-2 py-0.5 rounded">${p}</span>`
    ).join('');

    const derivativesHTML = (song.derivatives?.secondhandsongs || []).map(d =>
      `<li>${d.title} by ${d.artist}</li>`
    ).join('');

    // Build the card HTML
    const card = document.createElement('div');
    card.className = 'bg-white p-4 rounded shadow relative border';
    card.setAttribute('data-song-title', song.title);

    card.innerHTML = `
      <h3 class="text-lg font-bold">${safe(song.title)}</h3>
      <p class="text-sm mb-2"><strong>${safe(song.artist)}</strong></p>
      <button class="toggle-card absolute top-2 right-2 text-xs bg-gray-200 px-2 py-1 rounded">Collapse</button>
      <div class="card-content expanded mt-2 space-y-3">
        <p><strong>Album:</strong> ${safe(song.album)}</p>
        <p><strong>Release Year:</strong> ${safe(song.release_year)}</p>
        <div><strong>Label:</strong>
          <div class="flex flex-wrap gap-2 mt-1">${song.label ? `<span class="bg-orange-100 text-orange-800 text-xs px-2 py-0.5 rounded">${song.label}</span>` : ''}</div>
        </div>
        ${publishersHTML ? `<div><strong>Publishers:</strong><div class="flex flex-wrap gap-2 mt-1">${publishersHTML}</div></div>` : ''}
        <div><strong>Genres:</strong><div class="flex flex-wrap gap-2 mt-1">${genresHTML}</div></div>
        <div><strong>Contributors:</strong><ul class="mt-1 space-y-1">${contributorsHTML}</ul></div>
        ${derivativesHTML ? `<div><strong>Derivatives:</strong><ul>${derivativesHTML}</ul></div>` : ''}
      </div>
    `;

    grid.appendChild(card);
  });

  // Append grid to container
  container.appendChild(grid);

  // Show controls (Expand/Collapse buttons) if applicable
  if (controlsId) {
    document.getElementById(controlsId).classList.remove('hidden');
  }

  // ✅ Add toggle functionality for Collapse/Expand per card
  container.querySelectorAll('.toggle-card').forEach(btn => {
    btn.addEventListener('click', () => {
      const content = btn.nextElementSibling;
      content.classList.toggle('collapsed');
      content.classList.toggle('expanded');
      btn.textContent = content.classList.contains('collapsed') ? 'Expand' : 'Collapse';
    });
  });
}


// Insights
function displayInsights(insights, containerId) {
  const div = document.getElementById(containerId);
  div.innerHTML = '<h3 class="text-xl font-semibold mb-2">Derived Insights</h3><p class="text-sm text-gray-500 mb-2">Click an insight to highlight applicable songs</p>';
  if (!insights || !insights.shared) return;

  if (insights.summary) {
    div.innerHTML += `<p class="mb-3 text-gray-700">Songs: ${insights.summary.total_songs}, Unique Contributors: ${insights.summary.unique_contributors}, Unique Labels: ${insights.summary.unique_labels}</p>`;
  }

  if (insights.patterns && insights.patterns.clusters.length) {
    div.innerHTML += `<h4 class="font-semibold mt-3">Clustering</h4>`;
    insights.patterns.clusters.forEach(cluster => {
      div.innerHTML += `<span class="insight-item" data-songs="${cluster.songs.join(',')}">Cluster: ${cluster.names.join(' & ')} (${cluster.songs.length})</span>`;
    });
  }

  if (insights.patterns && insights.patterns.connectors.length) {
    div.innerHTML += `<h4 class="font-semibold mt-3">Linking</h4>`;
    insights.patterns.connectors.forEach(connector => {
      const linkText = `${connector.name} links ${connector.linked_contributors.slice(0, 3).join(' and ')}`;
      div.innerHTML += `<span class="insight-item" data-songs="${connector.songs.join(',')}">${linkText}</span>`;
    });
  }

  const sections = [
    { key: 'contributors', label: 'Shared Contributors' },
    { key: 'labels', label: 'Shared Labels' },
    { key: 'genres', label: 'Shared Genres' },
    { key: 'publishers', label: 'Shared Publishers' }
  ];
  sections.forEach(sec => {
    const arr = insights.shared[sec.key];
    if (arr && arr.length) {
      div.innerHTML += `<h4 class="font-semibold mt-3">${sec.label}</h4>`;
      arr.forEach(item => {
        div.innerHTML += `<span class="insight-item" data-songs="${item.songs.join(',')}">${item.name} (${item.count})</span>`;
      });
    }
  });

  if (insights.popularity_distribution) {
    div.innerHTML += `<h4 class="font-semibold mt-4">Popularity Distribution</h4>`;
    div.innerHTML += `<p class="mt-2"><strong>Track Popularity:</strong></p>`;
    for (const [range, songs] of Object.entries(insights.popularity_distribution.track)) {
      const colorClass = range === '0-25' ? 'bg-orange-100 text-orange-800' : range === '26-50' ? 'bg-yellow-100 text-yellow-800' : range === '51-75' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800';
      div.innerHTML += `<p><span class="${colorClass} px-2 py-0.5 rounded">${range}</span>: ${songs.join(', ')}</p>`;
    }
    div.innerHTML += `<p class="mt-2"><strong>Artist Popularity:</strong></p>`;
    for (const [range, artists] of Object.entries(insights.popularity_distribution.artist)) {
      const colorClass = range === '0-25' ? 'bg-orange-100 text-orange-800' : range === '26-50' ? 'bg-yellow-100 text-yellow-800' : range === '51-75' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800';
      div.innerHTML += `<p><span class="${colorClass} px-2 py-0.5 rounded">${range}</span>: ${artists.join(', ')}</p>`;
    }
  }

  div.innerHTML += `<h4 class="font-semibold mt-4">Top Entities</h4>`;
  div.innerHTML += `<p>Contributor: ${insights.top_entities.contributor || 'N/A'}, Label: ${insights.top_entities.label || 'N/A'}, Genre: ${insights.top_entities.genre || 'N/A'}</p>`;
  div.innerHTML += `<p class="mt-2">Songs with Derivatives: ${insights.extra_summary.derivative_count}</p>`;

  document.querySelectorAll('.insight-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const songs = btn.getAttribute('data-songs').split(',');
      document.querySelectorAll('[data-song-title]').forEach(card => {
        if (songs.includes(card.getAttribute('data-song-title'))) {
          card.classList.add('highlight');
        } else {
          card.classList.remove('highlight');
        }
      });
    });
  });
}

// Graph Buttons
document.getElementById('graphCurrentBtn').addEventListener('click', () => {
  if (currentData && currentData.songs) renderGraph(currentData.songs);
});
document.getElementById('graphDatabaseBtn').addEventListener('click', async () => {
  if (!databaseData) await loadDatabase();
  if (databaseData) renderGraph(databaseData);
});
document.getElementById('databaseGraphBtn').addEventListener('click', () => {
  if (databaseData) renderGraph(databaseData);
});

// Render Graph
function renderGraph(songs) {
  const container = document.getElementById('network');
  const nodes = [];
  const edges = [];
  const addedNodes = new Set();

  songs.forEach(song => {
    const songNode = `song-${song.title}`;
    if (!addedNodes.has(songNode)) {
      nodes.push({ id: songNode, label: song.title, color: colors.song });
      addedNodes.add(songNode);
    }
    (song.contributors || []).forEach(c => {
      const cNode = `contributor-${c.name}`;
      if (!addedNodes.has(cNode)) {
        nodes.push({ id: cNode, label: c.name, color: colors.contributor });
        addedNodes.add(cNode);
      }
      edges.push({ from: songNode, to: cNode });
    });
    if (song.label) {
      const lNode = `label-${song.label}`;
      if (!addedNodes.has(lNode)) {
        nodes.push({ id: lNode, label: song.label, color: colors.label });
        addedNodes.add(lNode);
      }
      edges.push({ from: songNode, to: lNode });
    }
    (song.publishers || []).forEach(pub => {
      const pNode = `publisher-${pub}`;
      if (!addedNodes.has(pNode)) {
        nodes.push({ id: pNode, label: pub, color: colors.publisher });
        addedNodes.add(pNode);
      }
      edges.push({ from: songNode, to: pNode });
    });
    (song.genres || []).forEach(g => {
      const gNode = `genre-${g}`;
      if (!addedNodes.has(gNode)) {
        nodes.push({ id: gNode, label: g, color: colors.genre });
        addedNodes.add(gNode);
      }
      edges.push({ from: songNode, to: gNode });
    });
  });

  const data = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) };
  const options = {
    physics: { enabled: true, stabilization: true },
    nodes: { shape: 'dot', size: 18, font: { size: 14 } },
    edges: { smooth: true }
  };

  network = new vis.Network(container, data, options);
  network.on('selectNode', params => {
    const nodeId = params.nodes[0];
    const node = data.nodes.get(nodeId);
    document.getElementById('details-panel').innerHTML = `<p><strong>${node.label}</strong></p>`;
  });
}
</script>
</body>
</html>
