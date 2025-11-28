import Song from "../models/Song.js";
import Artist from "../models/Artist.js";

// GET /songs - list all songs
export async function listSongs(req, res) {
  try {
    const songs = await Song.find()
      .populate("primaryArtist")
      .sort({ createdAt: -1 });

    res.json({ songs });
  } catch (err) {
    console.error("Error listing songs:", err);
    res.status(500).json({ error: "Server error retrieving songs" });
  }
}

// POST /songs - create a song with primary artist
export async function createSong(req, res) {
  try {
    const { title, primaryArtistName } = req.body;

    if (!title || !primaryArtistName) {
      return res.status(400).json({ error: "Missing fields" });
    }

    // find or create artist
    const artist = await Artist.findOneAndUpdate(
      { name: primaryArtistName },
      { name: primaryArtistName },
      { upsert: true, new: true }
    );

    const newSong = await Song.create({
      title,
      primaryArtist: artist._id,
      user: null, // not using auth yet
    });

    res.json({ message: "Song saved", song: newSong });
  } catch (err) {
    console.error("Error creating song:", err);
    res.status(500).json({ error: "Server error saving song" });
  }
}

// GET /songs/:id
export async function getSong(req, res) {
  try {
    const song = await Song.findById(req.params.id).populate("primaryArtist");
    if (!song) return res.status(404).json({ error: "Song not found" });

    res.json({ song });
  } catch (err) {
    console.error("Error retrieving song:", err);
    res.status(500).json({ error: "Server error retrieving song" });
  }
}

// DELETE /songs/:id
export async function deleteSong(req, res) {
  try {
    const deleted = await Song.findByIdAndDelete(req.params.id);
    if (!deleted) return res.status(404).json({ error: "Song not found" });

    res.json({ message: "Song deleted", deleted });
  } catch (err) {
    console.error("Error deleting song:", err);
    res.status(500).json({ error: "Server error deleting song" });
  }
}
