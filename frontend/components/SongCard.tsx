"use client";

import { useState } from "react";
import { Song } from "../context/SongContext";

type Props = {
  song: Song;
  highlighted?: boolean;
};

export default function SongCard({ song, highlighted = false }: Props) {
  const [open, setOpen] = useState(true);

  return (
    <div
      className={`song-card ${highlighted ? "highlight" : ""}`}
      data-song-title={song.title}
    >
      <div className="toggle-card" onClick={() => setOpen(!open)}>
        {open ? "Collapse" : "Expand"}
      </div>

      {/* Title & Artist */}
      <h3 style={{ fontSize: "1.4rem", fontWeight: 700, marginBottom: "0.25rem" }}>
        {song.title}
      </h3>
      <p style={{ fontWeight: 600, fontSize: "1.1rem", marginBottom: "1rem" }}>
        {song.artist}
      </p>

      <div className={`card-content ${open ? "" : "collapsed"}`}>
        {/* Album */}
        {song.album && (
          <p>
            <strong>Album:</strong> {song.album}
          </p>
        )}

        {/* Release Year */}
        {song.release_year && (
          <p style={{ marginTop: "0.25rem" }}>
            <strong>Release Year:</strong> {song.release_year}
          </p>
        )}

        {/* Label */}
        {song.label && (
          <p style={{ marginTop: "1rem" }}>
            <strong>Label:</strong>{" "}
            <span className="chip chip-label">{song.label}</span>
          </p>
        )}

        {/* Publishers */}
        {song.publishers && song.publishers.length > 0 && (
          <div style={{ marginTop: "1rem" }}>
            <strong>Publishers:</strong>
            <div style={{ marginTop: "0.5rem" }}>
              {song.publishers.map((p) => (
                <span key={p} className="chip chip-publisher">
                  {p}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Genres */}
        {song.genres && song.genres.length > 0 && (
          <div style={{ marginTop: "1rem" }}>
            <strong>Genres:</strong>
            <div style={{ marginTop: "0.5rem" }}>
              {song.genres.map((g) => (
                <span key={g} className="chip chip-genre">
                  {g}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Contributors */}
        {song.contributors && song.contributors.length > 0 && (
          <div style={{ marginTop: "1rem" }}>
            <strong>Contributors:</strong>
            <div style={{ marginTop: "0.75rem" }}>
              {song.contributors.map((c, idx) => (
                <div key={`${c.name}-${idx}`} style={{ marginBottom: "4px" }}>
                  <span style={{ fontWeight: 600 }}>{c.name}</span>{" "}
                  {c.roles.map((role) => (
                    <span key={role} className="chip chip-role">
                      {role}
                    </span>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Popularity (if available) */}
        {(song.spotify_popularity || song.artist_popularity) && (
          <div style={{ marginTop: "1rem", fontSize: "0.9rem", color: "#6b7280" }}>
            {song.spotify_popularity && (
              <p>
                <strong>Track Popularity:</strong> {song.spotify_popularity}
              </p>
            )}
            {song.artist_popularity && (
              <p>
                <strong>Artist Popularity:</strong> {song.artist_popularity}
              </p>
            )}
          </div>
        )}

        {/* Flags/Warnings */}
        {song.flags && song.flags.length > 0 && (
          <div
            style={{
              marginTop: "1rem",
              padding: "0.5rem",
              background: "#fef3c7",
              borderRadius: "0.5rem",
              fontSize: "0.85rem",
            }}
          >
            {song.flags.map((flag, idx) => (
              <p key={idx} style={{ color: "#92400e" }}>
                ⚠️ {flag.message}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}