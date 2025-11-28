// models/Song.js
import mongoose from "mongoose";

// ---- Embedded contributor subdocument ----
const contributorSchema = new mongoose.Schema(
  {
    artistId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Artist",
      required: true
    },
    role: { type: String, trim: true }
  },
  { _id: false }
);

// ---- Embedded source metadata ----
const sourceSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      enum: ["spotify", "musicbrainz", "discogs"]
    },
    id: String,
    fetchedAt: Date
  },
  { _id: false }
);

// ---- Song schema ----
const songSchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: false
    },
    title: {
      type: String,
      required: true,
      trim: true
    },
    primaryArtist: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Artist",
      required: true
    },
    contributors: [contributorSchema],
    genres: [String],
    labels: [String],
    sources: [sourceSchema]
  },
  { timestamps: true }
);

const Song = mongoose.model("Song", songSchema);
export default Song;
