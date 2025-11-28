"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import SongCard from "../../components/SongCard";
import { useSongContext, ApiResponse, SharedItem, Song } from "../../context/SongContext";

type ViewMode = "current" | "database";

export default function AnalyticsPage() {
    const { currentData } = useSongContext();
    const [databaseData, setDatabaseData] = useState<ApiResponse | null>(null);
    const [viewMode, setViewMode] = useState<ViewMode>("current");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [highlightedSongs, setHighlightedSongs] = useState<string[]>([]);

    const API = process.env.NEXT_PUBLIC_API_URL;

    // Load database data when switching to database view
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

    // Get active data based on view mode
    const activeData = viewMode === "current" ? currentData : databaseData;
    const songs = activeData?.songs || [];
    const insights = activeData?.derived_insights;

    // Handle clicking on an insight to highlight related songs
    function handleInsightClick(songTitles: string[]) {
        setHighlightedSongs((prev) =>
            JSON.stringify(prev) === JSON.stringify(songTitles) ? [] : songTitles
        );
    }

    return (
        <div className="section">
            <h2>Analytics Dashboard</h2>

            {/* View Mode Toggle */}
            <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1.5rem" }}>
                <button
                    onClick={() => setViewMode("current")}
                    className={viewMode === "current" ? "active-btn" : "inactive-btn"}
                    style={{ cursor: "pointer", border: "none" }}
                >
                    Current Input
                </button>
                <button
                    onClick={() => setViewMode("database")}
                    className={viewMode === "database" ? "active-btn" : "inactive-btn"}
                    style={{ cursor: "pointer", border: "none" }}
                >
                    Full Database
                </button>
                <Link href="/graph" className="btn btn-secondary" style={{ marginLeft: "auto" }}>
                    View Graph
                </Link>
            </div>

            {/* Loading/Error States */}
            {loading && <p>Loading database...</p>}
            {error && <p style={{ color: "#b91c1c" }}>{error}</p>}

            {/* No Data State */}
            {!loading && songs.length === 0 && (
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

            {/* Song Cards Grid */}
            {songs.length > 0 && (
                <>
                    <p style={{ marginBottom: "1rem", color: "#6b7280" }}>
                        Showing <strong>{songs.length}</strong> song{songs.length === 1 ? "" : "s"}
                    </p>

                    <div
                        style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
                            gap: "1rem",
                            marginBottom: "2rem",
                        }}
                    >
                        {songs.map((song, idx) => (
                            <SongCard
                                key={`${song.title}-${song.artist}-${idx}`}
                                song={song}
                                highlighted={highlightedSongs.includes(song.title)}
                            />
                        ))}
                    </div>
                </>
            )}

            {/* Derived Insights Panel */}
            {insights && songs.length > 0 && (
                <div className="insights-panel">
                    <h3>Derived Insights</h3>
                    <p className="text-sm" style={{ color: "#6b7280", marginBottom: "1rem" }}>
                        Click an insight to highlight applicable songs
                    </p>

                    {/* Summary Stats */}
                    {insights.summary && (
                        <p>
                            Songs: <strong>{insights.summary.total_songs}</strong>, Unique
                            Contributors: <strong>{insights.summary.unique_contributors}</strong>,
                            Unique Labels: <strong>{insights.summary.unique_labels}</strong>
                        </p>
                    )}

                    {/* Clustering */}
                    {insights.clustering && insights.clustering.length > 0 && (
                        <div style={{ marginTop: "1rem" }}>
                            <h4>Clustering</h4>
                            <p style={{ fontSize: "0.85rem", color: "#6b7280", marginBottom: "0.5rem" }}>
                                Contributors who worked together on multiple songs
                            </p>
                            {insights.clustering.map((cluster, idx) => (
                                <span
                                    key={idx}
                                    className="insight-item"
                                    onClick={() => handleInsightClick([])} // Would need song mapping
                                >
                                    {cluster.names.join(", ")} worked on {cluster.song_count} songs together
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Linking */}
                    {insights.linking && insights.linking.length > 0 && (
                        <div style={{ marginTop: "1rem" }}>
                            <h4>Linking</h4>
                            <p style={{ fontSize: "0.85rem", color: "#6b7280", marginBottom: "0.5rem" }}>
                                A contributor who connects others that don&apos;t otherwise share a song
                            </p>
                            {insights.linking.map((link, idx) => (
                                <span key={idx} className="insight-item">
                                    {link.linker} links {link.linked.join(", ")}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Shared Contributors */}
                    {insights.shared?.contributors && insights.shared.contributors.length > 0 && (
                        <SharedSection
                            title="Shared Contributors"
                            items={insights.shared.contributors}
                            onItemClick={handleInsightClick}
                        />
                    )}

                    {/* Shared Labels */}
                    {insights.shared?.labels && insights.shared.labels.length > 0 && (
                        <SharedSection
                            title="Shared Labels"
                            items={insights.shared.labels}
                            onItemClick={handleInsightClick}
                        />
                    )}

                    {/* Shared Genres */}
                    {insights.shared?.genres && insights.shared.genres.length > 0 && (
                        <SharedSection
                            title="Shared Genres"
                            items={insights.shared.genres}
                            onItemClick={handleInsightClick}
                        />
                    )}

                    {/* Shared Publishers */}
                    {insights.shared?.publishers && insights.shared.publishers.length > 0 && (
                        <SharedSection
                            title="Shared Publishers"
                            items={insights.shared.publishers}
                            onItemClick={handleInsightClick}
                        />
                    )}

                    {/* Popularity Distribution */}
                    {insights.popularity_distribution && (
                        <div style={{ marginTop: "1.5rem" }}>
                            <h4>Popularity Distribution</h4>

                            {Object.keys(insights.popularity_distribution.track).length > 0 && (
                                <>
                                    <p style={{ marginTop: "0.5rem" }}>
                                        <strong>Track Popularity:</strong>
                                    </p>
                                    {Object.entries(insights.popularity_distribution.track).map(
                                        ([range, trackList]) => (
                                            <p key={range} style={{ fontSize: "0.9rem" }}>
                                                <span
                                                    style={{
                                                        fontWeight: 600,
                                                        background: getPopularityColor(range),
                                                        padding: "2px 6px",
                                                        borderRadius: "4px",
                                                    }}
                                                >
                                                    {range}
                                                </span>
                                                : {trackList.join(", ")}
                                            </p>
                                        )
                                    )}
                                </>
                            )}

                            {Object.keys(insights.popularity_distribution.artist).length > 0 && (
                                <>
                                    <p style={{ marginTop: "0.75rem" }}>
                                        <strong>Artist Popularity:</strong>
                                    </p>
                                    {Object.entries(insights.popularity_distribution.artist).map(
                                        ([range, artistList]) => (
                                            <p key={range} style={{ fontSize: "0.9rem" }}>
                                                <span
                                                    style={{
                                                        fontWeight: 600,
                                                        background: getPopularityColor(range),
                                                        padding: "2px 6px",
                                                        borderRadius: "4px",
                                                    }}
                                                >
                                                    {range}
                                                </span>
                                                : {artistList.join(", ")}
                                            </p>
                                        )
                                    )}
                                </>
                            )}
                        </div>
                    )}

                    {/* Extra Summary */}
                    {insights.extra_summary && (
                        <div style={{ marginTop: "1.5rem" }}>
                            <h4>Extra Summary</h4>
                            <p>
                                Songs with derivatives (covers, samples):{" "}
                                <strong>{insights.extra_summary.derivative_count}</strong>
                            </p>
                            {Object.keys(insights.extra_summary.role_tally).length > 0 && (
                                <p style={{ marginTop: "0.5rem" }}>
                                    <strong>Role counts:</strong>{" "}
                                    {Object.entries(insights.extra_summary.role_tally)
                                        .map(([role, count]) => `${role} (${count})`)
                                        .join(", ")}
                                </p>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

// Helper component for shared sections
function SharedSection({
    title,
    items,
    onItemClick,
}: {
    title: string;
    items: SharedItem[];
    onItemClick: (songs: string[]) => void;
}) {
    return (
        <div style={{ marginTop: "1rem" }}>
            <h4>{title}</h4>
            <div>
                {items.map((item) => (
                    <span
                        key={item.name}
                        className="insight-item"
                        onClick={() => onItemClick(item.songs)}
                        title={`Songs: ${item.songs.join(", ")}`}
                    >
                        {item.name} ({item.count})
                    </span>
                ))}
            </div>
        </div>
    );
}

// Helper to get background color for popularity ranges
function getPopularityColor(range: string): string {
    if (range.includes("76-100")) return "#d1fae5";
    if (range.includes("51-75")) return "#fef9c3";
    if (range.includes("26-50")) return "#fef3c7";
    return "#fee2e2";
}