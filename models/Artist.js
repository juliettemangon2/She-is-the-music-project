import mongoose from "mongoose";

const artistSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: true,
      trim: true,
      index: true,
    },
    externalIds: {
      spotify: { type: String, default: null },
      musicbrainz: { type: String, default: null },
      discogs: { type: String, default: null }
    }
  },
  {
    timestamps: true
  }
);

const Artist = mongoose.model("Artist", artistSchema);
export default Artist;
