"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import SongCard from "../../components/SongCard";
import { ApiResponse, Song } from "../../context/SongContext";

export default function DatabasePage() {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const API = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    loadDatabase();
  }, []);

  async function loadDatabase() {
    if (!API) {
      setError("API URL is not configured.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/database`);
      if (!res.ok) {
        setError("Server returned an error.");
        setLoading(false);
        return;
      }
      const json: ApiResponse = await res.json();
      setData(json);
    } catch (err) {
      console.error(err);
      setError("Network error loading database.");
    } finally {
      setLoading(false);
    }
  }

  const songs = data?.songs || [];

  return (
    <div className="section">
      <h2>Database</h2>

      <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
        <Link href="/analytics" className="btn btn-primary">
          View Analytics
        </Link>
        <Link href="/graph" className="btn btn-secondary">
          View Graph
        </Link>
        <button
          onClick={loadDatabase}
          className="btn btn-secondary"
          style={{ marginLeft: "auto" }}
        >
          Refresh
        </button>
      </div>

      {loading && <p>Loading database...</p>}
      {error && <p style={{ color: "#b91c1c" }}>{error}</p>}

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
            No songs in database yet.
          </p>
          <Link href="/song-input" className="btn btn-primary">
            Add Songs
          </Link>
        </div>
      )}

      {songs.length > 0 && (
        <>
          <p style={{ marginBottom: "1rem", color: "#6b7280" }}>
            Total songs stored: <strong>{songs.length}</strong>
          </p>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
              gap: "1rem",
            }}
          >
            {songs.map((song, idx) => (
              <SongCard key={`${song.title}-${song.artist}-${idx}`} song={song} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}