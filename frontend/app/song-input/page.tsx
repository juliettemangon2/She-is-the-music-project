"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { useSongContext, ApiResponse } from "../../context/SongContext";

type SongInput = {
  artist: string;
  title: string;
};

type FetchStatus = "idle" | "loading" | "success" | "error";

export default function SongInputPage() {
  const [songs, setSongs] = useState<SongInput[]>([{ artist: "", title: "" }]);
  const [status, setStatus] = useState<FetchStatus>("idle");
  const [message, setMessage] = useState<string>("");
  const router = useRouter();
  const { setCurrentData, setIsLoading } = useSongContext();

  const API = process.env.NEXT_PUBLIC_API_URL;

  function updateSong(index: number, field: "artist" | "title", value: string) {
    setSongs((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: value };
      return copy;
    });
  }

  function addRow() {
    setSongs((prev) => [...prev, { artist: "", title: "" }]);
  }

  function removeRow(index: number) {
    setSongs((prev) => prev.filter((_, i) => i !== index));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!API) {
      setStatus("error");
      setMessage("API URL is not configured. Set NEXT_PUBLIC_API_URL in .env.local");
      return;
    }

    const cleaned = songs.filter(
      (s) => s.artist.trim().length && s.title.trim().length
    );
    if (cleaned.length === 0) {
      setStatus("error");
      setMessage("Please enter at least one artist and title.");
      return;
    }

    setStatus("loading");
    setIsLoading(true);
    setMessage("");

    try {
      const res = await fetch(`${API}/api/fetch-multiple`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ songs: cleaned }),
      });

      if (!res.ok) {
        setStatus("error");
        setMessage("Server returned an error. Check console for details.");
        setIsLoading(false);
        return;
      }

      const data: ApiResponse = await res.json();
      
      // Store in context for other pages to use
      setCurrentData(data);
      
      const count = data.songs?.length ?? cleaned.length;
      setStatus("success");
      setMessage(`Done! Fetched metadata for ${count} song${count === 1 ? "" : "s"}.`);
    } catch (err) {
      console.error(err);
      setStatus("error");
      setMessage("Network error while fetching metadata.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="section">
      <h2>Song Input</h2>

      <form onSubmit={onSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {songs.map((song, index) => (
            <div
              key={index}
              style={{
                background: index === 0 ? "#ffffff" : "#f9fafb",
                padding: "1rem",
                borderRadius: "0.75rem",
                border: "1px solid #e5e7eb",
                display: "flex",
                gap: "0.75rem",
                alignItems: "center",
              }}
            >
              <input
                type="text"
                placeholder="Artist Name"
                value={song.artist}
                onChange={(e) => updateSong(index, "artist", e.target.value)}
                style={{
                  flex: 1,
                  borderRadius: "0.5rem",
                  border: "1px solid #d1d5db",
                  padding: "0.5rem 0.75rem",
                  fontSize: "1rem",
                }}
              />
              <input
                type="text"
                placeholder="Song Title"
                value={song.title}
                onChange={(e) => updateSong(index, "title", e.target.value)}
                style={{
                  flex: 1,
                  borderRadius: "0.5rem",
                  border: "1px solid #d1d5db",
                  padding: "0.5rem 0.75rem",
                  fontSize: "1rem",
                }}
              />
              {songs.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeRow(index)}
                  className="btn"
                  style={{ background: "#fee2e2", color: "#b91c1c" }}
                >
                  Remove
                </button>
              )}
            </div>
          ))}
        </div>

        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button
            type="button"
            onClick={addRow}
            className="btn"
            style={{ background: "#fdf2f8", color: "#1d4ed8", border: "1px solid #e5e7eb" }}
          >
            + Add Song
          </button>
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={status === "loading"}
          >
            {status === "loading" ? "Fetching..." : "Compare Songs"}
          </button>
        </div>
      </form>

      {/* Status area */}
      <div style={{ marginTop: "1.5rem" }}>
        {status === "success" && (
          <div
            style={{
              borderRadius: "0.75rem",
              padding: "1rem 1.25rem",
              background: "#ecfdf3",
              border: "1px solid #bbf7d0",
            }}
          >
            <p style={{ marginBottom: "0.75rem", fontWeight: 500 }}>{message}</p>
            <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
              <button
                className="btn btn-primary"
                type="button"
                onClick={() => router.push("/analytics")}
              >
                View Details & Insights
              </button>
              <button
                className="btn btn-secondary"
                type="button"
                onClick={() => router.push("/graph")}
              >
                Visualize Graph
              </button>
            </div>
          </div>
        )}

        {status === "error" && (
          <p style={{ color: "#b91c1c", marginTop: "0.5rem" }}>{message}</p>
        )}

        {status === "loading" && (
          <div style={{ marginTop: "0.5rem" }}>
            <p>Fetching metadata from Spotify, MusicBrainz, Discogs, and more...</p>
            <p style={{ fontSize: "0.85rem", color: "#6b7280" }}>
              This may take a few seconds per song.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}