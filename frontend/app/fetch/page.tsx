"use client";

import { useState } from "react";

type Contributor = {
    name: string;
    roles: string[];
    sources: string[];
};

type Derivatives = {
    secondhandsongs: {
        title: string;
        artist: string;
        relation_type: string;
        uri: string;
    }[];
    discogs_master?: any;
};

type SongResult = {
    artist: string;
    title: string;
    album: string | null;
    release_year: number | null;
    label: string | null;
    spotify_popularity: number;
    artist_popularity: number;
    genres: string[];
    contributors: Contributor[];
    publishers: string[];
    derivatives: Derivatives;
    flags: { type: string; message: string }[];
};

export default function FetchPage() {
    const [artist, setArtist] = useState("");
    const [title, setTitle] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<SongResult | null>(null);
    const [error, setError] = useState("");

    async function fetchSong() {
        setLoading(true);
        setError("");
        setResult(null);

        try {
            const API = process.env.NEXT_PUBLIC_API_URL;

            const res = await fetch(`${API}/api/fetch-one`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ artist, title })
            });


            if (!res.ok) {
                setError("Request failed");
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
                Fetch Song Metadata
            </h1>

            <div style={{ marginBottom: "1rem" }}>
                <label>Artist</label>
                <input
                    value={artist}
                    onChange={(e) => setArtist(e.target.value)}
                    style={{
                        display: "block",
                        marginTop: "0.25rem",
                        padding: "0.5rem",
                        width: "300px",
                    }}
                />

                <label style={{ marginTop: "1rem", display: "block" }}>Title</label>
                <input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    style={{
                        display: "block",
                        marginTop: "0.25rem",
                        padding: "0.5rem",
                        width: "300px",
                    }}
                />

                <button
                    onClick={fetchSong}
                    disabled={loading}
                    style={{
                        marginTop: "1rem",
                        padding: "0.75rem 1.25rem",
                        background: "black",
                        color: "white",
                        cursor: "pointer",
                        borderRadius: "4px",
                        border: "none",
                    }}
                >
                    {loading ? "Loading..." : "Fetch"}
                </button>
            </div>

            {error && <p style={{ color: "red" }}>{error}</p>}

            {result && (
                <div
                    style={{
                        marginTop: "2rem",
                        padding: "1.5rem",
                        background: "#f8f8f8",
                        borderRadius: "6px",
                    }}
                >
                    <h2 style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>
                        {result.title} – {result.artist}
                    </h2>

                    <p>
                        <strong>Album:</strong> {result.album || "N/A"}
                    </p>
                    <p>
                        <strong>Year:</strong> {result.release_year || "N/A"}
                    </p>
                    <p>
                        <strong>Label:</strong> {result.label || "N/A"}
                    </p>
                    <p>
                        <strong>Genres:</strong>{" "}
                        {result.genres.length ? result.genres.join(", ") : "None"}
                    </p>

                    <hr style={{ margin: "1rem 0" }} />

                    <h3>Contributors</h3>
                    {result.contributors.length === 0 ? (
                        <p>None found</p>
                    ) : (
                        <ul>
                            {result.contributors.map((c, i) => (
                                <li key={i}>
                                    <strong>{c.name}</strong> — {c.roles.join(", ")} (
                                    {c.sources.join(", ")})
                                </li>
                            ))}
                        </ul>
                    )}

                    <h3 style={{ marginTop: "1rem" }}>Derivatives</h3>
                    {result.derivatives.secondhandsongs.length === 0 ? (
                        <p>No derivatives found</p>
                    ) : (
                        <ul>
                            {result.derivatives.secondhandsongs.map((d, i) => (
                                <li key={i}>
                                    <strong>{d.title}</strong> — {d.artist} ({d.relation_type})
                                </li>
                            ))}
                        </ul>
                    )}

                    <h3 style={{ marginTop: "1rem" }}>Flags</h3>
                    {result.flags.length === 0 ? (
                        <p>No insight flags</p>
                    ) : (
                        <ul>
                            {result.flags.map((f, i) => (
                                <li key={i}>
                                    <strong>{f.type}:</strong> {f.message}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            )}
        </div>
    );
}
