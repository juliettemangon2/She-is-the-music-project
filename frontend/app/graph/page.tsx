"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSongContext, ApiResponse, Song } from "../../context/SongContext";

// Node colors matching your mockup
const colors = {
  song: "#93c5fd", // light blue
  contributor: "#fcd34d", // yellow/gold
  label: "#fb923c", // orange
  publisher: "#f472b6", // pink
  genre: "#34d399", // green/teal
};

type ViewMode = "current" | "database";

type FilterState = {
  contributors: boolean;
  labels: boolean;
  publishers: boolean;
  genres: boolean;
};

type SelectedNode = {
  id: string;
  label: string;
  type: string;
  song?: Song;
};

export default function GraphPage() {
  const { currentData } = useSongContext();
  const [databaseData, setDatabaseData] = useState<ApiResponse | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("current");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);
  const [filters, setFilters] = useState<FilterState>({
    contributors: true,
    labels: true,
    publishers: true,
    genres: true,
  });
  const [trackPopMin, setTrackPopMin] = useState(0);
  const [artistPopMin, setArtistPopMin] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<any>(null);

  const API = process.env.NEXT_PUBLIC_API_URL;

  // Load database when switching to database mode
  useEffect(() => {
    if (viewMode === "database" && !databaseData) {
      loadDatabase();
    }
  }, [viewMode]);

  async function loadDatabase() {
    if (!API) {
      setError("API URL is not configured.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/database`);
      if (!res.ok) {
        setError("Server returned an error.");
        return;
      }
      const json: ApiResponse = await res.json();
      setDatabaseData(json);
    } catch (err) {
      console.error(err);
      setError("Network error loading database.");
    } finally {
      setLoading(false);
    }
  }

  // Render graph when data or filters change
  useEffect(() => {
    const activeData = viewMode === "current" ? currentData : databaseData;
    if (activeData?.songs && containerRef.current) {
      renderGraph(activeData.songs);
    }
  }, [viewMode, currentData, databaseData, filters, trackPopMin, artistPopMin]);

  async function renderGraph(songs: Song[]) {
    // Dynamically import vis-network (client-side only)
    const { Network, DataSet } = await import("vis-network/standalone") as any;

    const nodes: any[] = [];
    const edges: any[] = [];
    const addedNodes = new Set<string>();

    // Filter songs by popularity
    const filteredSongs = songs.filter((song) => {
      const trackPop = song.spotify_popularity ?? 0;
      const artistPop = song.artist_popularity ?? 0;
      return trackPop >= trackPopMin && artistPop >= artistPopMin;
    });

    filteredSongs.forEach((song) => {
      const songNodeId = `song-${song.title}-${song.artist}`;
      if (!addedNodes.has(songNodeId)) {
        nodes.push({
          id: songNodeId,
          label: song.title,
          color: colors.song,
          type: "song",
          songData: song,
        });
        addedNodes.add(songNodeId);
      }

      // Contributors
      if (filters.contributors && song.contributors) {
        song.contributors.forEach((c) => {
          const cNodeId = `contributor-${c.name}`;
          if (!addedNodes.has(cNodeId)) {
            nodes.push({
              id: cNodeId,
              label: c.name,
              color: colors.contributor,
              type: "contributor",
            });
            addedNodes.add(cNodeId);
          }
          edges.push({ from: songNodeId, to: cNodeId });
        });
      }

      // Label
      if (filters.labels && song.label) {
        const lNodeId = `label-${song.label}`;
        if (!addedNodes.has(lNodeId)) {
          nodes.push({
            id: lNodeId,
            label: song.label,
            color: colors.label,
            type: "label",
          });
          addedNodes.add(lNodeId);
        }
        edges.push({ from: songNodeId, to: lNodeId });
      }

      // Publishers
      if (filters.publishers && song.publishers) {
        song.publishers.forEach((pub) => {
          const pNodeId = `publisher-${pub}`;
          if (!addedNodes.has(pNodeId)) {
            nodes.push({
              id: pNodeId,
              label: pub,
              color: colors.publisher,
              type: "publisher",
            });
            addedNodes.add(pNodeId);
          }
          edges.push({ from: songNodeId, to: pNodeId });
        });
      }

      // Genres
      if (filters.genres && song.genres) {
        song.genres.forEach((g) => {
          const gNodeId = `genre-${g}`;
          if (!addedNodes.has(gNodeId)) {
            nodes.push({
              id: gNodeId,
              label: g,
              color: colors.genre,
              type: "genre",
            });
            addedNodes.add(gNodeId);
          }
          edges.push({ from: songNodeId, to: gNodeId });
        });
      }
    });

    const data = {
      nodes: new DataSet(nodes),
      edges: new DataSet(edges),
    };

    const options = {
      physics: {
        enabled: true,
        stabilization: { iterations: 100 },
        barnesHut: {
          gravitationalConstant: -3000,
          springLength: 100,
        },
      },
      nodes: {
        shape: "dot",
        size: 18,
        font: { size: 14, color: "#333" },
        borderWidth: 2,
        shadow: true,
      },
      edges: {
        smooth: { type: "continuous" },
        color: { color: "#ccc", highlight: "#2563eb" },
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
      },
    };

    if (containerRef.current) {
      // Destroy previous network if exists
      if (networkRef.current) {
        networkRef.current.destroy();
      }

      networkRef.current = new Network(containerRef.current, data, options);

      // Handle node selection
      networkRef.current.on("selectNode", (params: any) => {
        const nodeId = params.nodes[0];
        const node = data.nodes.get(nodeId) as any;
        if (node) {
          setSelectedNode({
            id: node.id,
            label: node.label,
            type: node.type,
            song: node.songData,
          });
        }
      });

      networkRef.current.on("deselectNode", () => {
        setSelectedNode(null);
      });
    }
  }

  function resetFilters() {
    setFilters({
      contributors: true,
      labels: true,
      publishers: true,
      genres: true,
    });
    setTrackPopMin(0);
    setArtistPopMin(0);
  }

  const activeData = viewMode === "current" ? currentData : databaseData;
  const hasSongs = (activeData?.songs?.length ?? 0) > 0;

  return (
    <div className="section">
      <h2>Graph Visualization</h2>

      {/* View Mode Toggle */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", flexWrap: "wrap" }}>
        <button
          onClick={() => setViewMode("current")}
          className={viewMode === "current" ? "active-btn" : "inactive-btn"}
          style={{ cursor: "pointer", border: "none" }}
        >
          Graph Current Input
        </button>
        <button
          onClick={() => setViewMode("database")}
          className={viewMode === "database" ? "active-btn" : "inactive-btn"}
          style={{ cursor: "pointer", border: "none" }}
        >
          Graph Database
        </button>
        <button
          onClick={resetFilters}
          className="btn btn-secondary"
          style={{ marginLeft: "0.5rem" }}
        >
          Reset Filters
        </button>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: "1.5rem", marginBottom: "1rem", flexWrap: "wrap", alignItems: "center" }}>
        <label style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
          <input
            type="checkbox"
            checked={filters.contributors}
            onChange={(e) => setFilters({ ...filters, contributors: e.target.checked })}
          />
          Contributors
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
          <input
            type="checkbox"
            checked={filters.labels}
            onChange={(e) => setFilters({ ...filters, labels: e.target.checked })}
          />
          Labels
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
          <input
            type="checkbox"
            checked={filters.publishers}
            onChange={(e) => setFilters({ ...filters, publishers: e.target.checked })}
          />
          Publishers
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
          <input
            type="checkbox"
            checked={filters.genres}
            onChange={(e) => setFilters({ ...filters, genres: e.target.checked })}
          />
          Genres
        </label>

        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span>Track Pop:</span>
          <input
            type="range"
            min={0}
            max={100}
            value={trackPopMin}
            onChange={(e) => setTrackPopMin(Number(e.target.value))}
            style={{ width: "80px" }}
          />
          <span>{trackPopMin}+</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span>Artist Pop:</span>
          <input
            type="range"
            min={0}
            max={100}
            value={artistPopMin}
            onChange={(e) => setArtistPopMin(Number(e.target.value))}
            style={{ width: "80px" }}
          />
          <span>{artistPopMin}+</span>
        </div>
      </div>

      {/* Loading/Error */}
      {loading && <p>Loading database...</p>}
      {error && <p style={{ color: "#b91c1c" }}>{error}</p>}

      {/* No Data */}
      {!loading && !hasSongs && (
        <div
          style={{
            padding: "2rem",
            background: "#f9fafb",
            borderRadius: "1rem",
            textAlign: "center",
          }}
        >
          <p style={{ marginBottom: "1rem", color: "#6b7280" }}>
            {viewMode === "current"
              ? "No songs in current session. Add some songs first!"
              : "No songs in database yet."}
          </p>
          <Link href="/song-input" className="btn btn-primary">
            Add Songs
          </Link>
        </div>
      )}

      {/* Graph Container + Details Panel */}
      {hasSongs && (
        <div style={{ display: "flex", gap: "1rem" }}>
          {/* Network Graph */}
          <div
            ref={containerRef}
            style={{
              flex: 1,
              height: "500px",
              borderRadius: "0.75rem",
              border: "1px solid #e5e7eb",
              background: "#ffffff",
            }}
          />

          {/* Right Panel: Legend + Node Details */}
          <div style={{ width: "260px", flexShrink: 0 }}>
            {/* Legend */}
            <div
              style={{
                background: "#f9fafb",
                borderRadius: "0.75rem",
                padding: "1rem",
                marginBottom: "1rem",
                border: "1px solid #e5e7eb",
              }}
            >
              <h4 style={{ marginBottom: "0.75rem", fontWeight: 600 }}>Legend</h4>
              <LegendItem color={colors.song} label="Song" />
              <LegendItem color={colors.contributor} label="Contributor" />
              <LegendItem color={colors.label} label="Label" />
              <LegendItem color={colors.publisher} label="Publisher" />
              <LegendItem color={colors.genre} label="Genre" />
            </div>

            {/* Node Details */}
            <div
              style={{
                background: "#f9fafb",
                borderRadius: "0.75rem",
                padding: "1rem",
                border: "1px solid #e5e7eb",
              }}
            >
              <h4 style={{ marginBottom: "0.75rem", fontWeight: 600 }}>Node Details</h4>
              {selectedNode ? (
                <div>
                  <p style={{ fontWeight: 700, fontSize: "1.1rem" }}>{selectedNode.label}</p>
                  <p style={{ color: "#6b7280", fontSize: "0.9rem", marginBottom: "0.5rem" }}>
                    Type: {selectedNode.type}
                  </p>
                  {selectedNode.song && (
                    <>
                      <p>
                        <strong>Artist:</strong> {selectedNode.song.artist}
                      </p>
                      {selectedNode.song.album && (
                        <p>
                          <strong>Album:</strong> {selectedNode.song.album}
                        </p>
                      )}
                      {selectedNode.song.label && (
                        <p>
                          <strong>Label:</strong> {selectedNode.song.label}
                        </p>
                      )}
                      {selectedNode.song.genres && selectedNode.song.genres.length > 0 && (
                        <p>
                          <strong>Genres:</strong> {selectedNode.song.genres.join(", ")}
                        </p>
                      )}
                      {selectedNode.song.spotify_popularity && (
                        <p>
                          <strong>Track Popularity:</strong> {selectedNode.song.spotify_popularity}
                        </p>
                      )}
                      {selectedNode.song.artist_popularity && (
                        <p>
                          <strong>Artist Popularity:</strong> {selectedNode.song.artist_popularity}
                        </p>
                      )}
                    </>
                  )}
                </div>
              ) : (
                <p style={{ color: "#9ca3af" }}>Click a node to see details</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.4rem" }}>
      <div
        style={{
          width: "14px",
          height: "14px",
          borderRadius: "50%",
          background: color,
        }}
      />
      <span style={{ fontSize: "0.9rem" }}>{label}</span>
    </div>
  );
}