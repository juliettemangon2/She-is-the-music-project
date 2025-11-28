"use client";

import { useState } from "react";

type SongInput = {
    artist: string;
    title: string;
};

type Contributor = {
    name: string;
    roles: string[];
    songs?: string[];
};

type InsightData = {
    summary: any;
    shared: {
        contributors: Contributor[];
        labels: any[];
        genres: any[];
        publishers: any[];
    };
    popularity_distribution: {
        track: Record<string, string[]>;
        artist: Record<string, string[]>;
    };
    extra_summary: {
        role_tally: Record<string, number>;
        derivative_count: number;
    };
};

type SongResult = {
    artist: string;
    title: string;
    album: string | null;
    release_year: number | null;
    label: string | null;
    genres: string[];
    contributors: Contributor[];
    publishers: string[];
    derivatives: any;
    flags: any[];
};

export default function FetchMultiplePage() {
    const [songs, setSongs] = useState<SongInput[]>([
        { artist: "", title: "" }
    ]);

    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<{
        songs: SongResult[];
        derived_insights: InsightData | null;
    } | null>(null);

    const [error, setError] = useState("");

    // Add new row
    function addSongRow() {
        setSongs([...songs, { artist: "", title: "" }]);
    }

    // Remove row
    function removeSongRow(index: number) {
        setSongs(songs.filter((_, i) => i !== index));
    }

    // Update a row
    function updateRow(index: number, key: "artist" | "title", value: string) {
        const newSongs = [...songs];
        newSongs[index][key] = value;
        setSongs(newSongs);
    }

    // Submit request
    async function fetchMultiple() {
        setLoading(true);
        setError("");
        setResult(null);

        try {
            const API = process.env.NEXT_PUBLIC_API_URL;

            const res = await fetch(`${API}/api/fetch-multiple`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ songs })
            });

            if (!res.ok) {
                setError("Failed to fetch metadata");
                setLoading(false);
                return;
            }

            const data = await res.json();
            setResult(data);
        } catch (e) {
            console.error(e);
            setError("Network error");
        }

        setLoading(false);
    }

    return (
        <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
            <h1 style={{ fontSize: "2rem", marginBottom: "1rem" }}>
                Fetch Metadata for Multiple Songs
            </h1>

            {/* INPUT TABLE */}
            <div style={{ marginBottom: "1rem" }}>
                {songs.map((s, i) => (
                    <div
                        key={i}
                        style={{
                            display: "flex",
                            gap: "1rem",
                            marginBottom: "0.75rem",
                            alignItems: "center"
                        }}
                    >
                        <input
                            placeholder="Artist"
                            value={s.artist}
                            onChange={(e) =>
                                updateRow(i, "artist", e.target.value)
                            }
                            style={{
                                padding: "0.5rem",
                                width: "200px",
                                border: "1px solid #ccc"
                            }}
                        />

                        <input
                            placeholder="Title"
                            value={s.title}
                            onChange={(e) =>
                                updateRow(i, "title", e.target.value)
                            }
                            style={{
                                padding: "0.5rem",
                                width: "200px",
                                border: "1px solid #ccc"
                            }}
                        />

                        {songs.length > 1 && (
                            <button
                                onClick={() => removeSongRow(i)}
                                style={{
                                    background: "red",
                                    color: "white",
                                    border: "none",
                                    padding: "0.5rem",
                                    cursor: "pointer"
                                }}
                            >
                                ✕
                            </button>
                        )}
                    </div>
                ))}

                <button
                    onClick={addSongRow}
                    style={{
                        padding: "0.5rem 1rem",
                        background: "#444",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        marginBottom: "1rem"
                    }}
                >
                    + Add another song
                </button>

                <br />

                <button
                    onClick={fetchMultiple}
                    disabled={loading}
                    style={{
                        padding: "0.75rem 1.25rem",
                        background: "black",
                        color: "white",
                        borderRadius: "4px",
                        border: "none",
                        cursor: "pointer"
                    }}
                >
                    {loading ? "Loading..." : "Fetch Insights"}
                </button>
            </div>

            {error && <p style={{ color: "red" }}>{error}</p>}

            {/* METADATA RESULTS */}
            {result && (
                <div style={{ marginTop: "2rem" }}>
                    <h2 style={{ fontSize: "1.5rem" }}>Songs Returned</h2>

                    {result.songs.map((s, i) => (
                        <div
                            key={i}
                            style={{
                                background: "#f8f8f8",
                                padding: "1rem",
                                borderRadius: "6px",
                                marginBottom: "1rem"
                            }}
                        >
                            <strong>
                                {s.title} – {s.artist}
                            </strong>
                            <p>
                                <strong>Label:</strong> {s.label || "N/A"}
                            </p>
                            <p>
                                <strong>Genres:</strong>{" "}
                                {s.genres.join(", ") || "None"}
                            </p>

                            <h4>Contributors</h4>
                            <ul>
                                {s.contributors.map((c, j) => (
                                    <li key={j}>
                                        <strong>{c.name}</strong>:{" "}
                                        {c.roles.join(", ")}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}

                    {/* INSIGHTS SECTION */}
                    {result.derived_insights && (
                        <div style={{ marginTop: "2rem" }}>
                            <h2 style={{ fontSize: "1.6rem" }}>
                                Derived Insights
                            </h2>

                            <h3>Summary</h3>
                            <pre>{JSON.stringify(result.derived_insights.summary, null, 2)}</pre>

                            <h3>Shared Contributors</h3>
                            <pre>{JSON.stringify(result.derived_insights.shared.contributors, null, 2)}</pre>

                            <h3>Shared Labels</h3>
                            <pre>{JSON.stringify(result.derived_insights.shared.labels, null, 2)}</pre>

                            <h3>Shared Genres</h3>
                            <pre>{JSON.stringify(result.derived_insights.shared.genres, null, 2)}</pre>

                            <h3>Role Tally</h3>
                            <pre>{JSON.stringify(result.derived_insights.extra_summary.role_tally, null, 2)}</pre>

                            <h3>Popularity Distribution</h3>
                            <pre>{JSON.stringify(result.derived_insights.popularity_distribution, null, 2)}</pre>

                            <h3>Derivative Count</h3>
                            <pre>{JSON.stringify(result.derived_insights.extra_summary.derivative_count, null, 2)}</pre>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
