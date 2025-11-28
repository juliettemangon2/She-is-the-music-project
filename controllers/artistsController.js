import Artist from "../models/Artist.js";

// GET /artists - list all artists
export async function listArtists(req, res) {
  try {
    const artists = await Artist.find().sort({ name: 1 });
    res.json({ artists });
  } catch (err) {
    console.error("Error listing artists:", err);
    res.status(500).json({ error: "Server error retrieving artists" });
  }
}

// POST /artists - create or upsert an artist
export async function createArtist(req, res) {
  try {
    const { name } = req.body;
    if (!name) return res.status(400).json({ error: "Name is required" });

    const artist = await Artist.findOneAndUpdate(
      { name },
      { name },
      { upsert: true, new: true }
    );

    res.json({ message: "Artist saved", artist });
  } catch (err) {
    console.error("Error creating artist:", err);
    res.status(500).json({ error: "Server error saving artist" });
  }
}

// GET /artists/:id - get one artist
export async function getArtist(req, res) {
  try {
    const artist = await Artist.findById(req.params.id);
    if (!artist) return res.status(404).json({ error: "Artist not found" });

    res.json({ artist });
  } catch (err) {
    console.error("Error retrieving artist:", err);
    res.status(500).json({ error: "Server error retrieving artist" });
  }
}

// DELETE /artists/:id - delete an artist
export async function deleteArtist(req, res) {
  try {
    const deleted = await Artist.findByIdAndDelete(req.params.id);
    if (!deleted) return res.status(404).json({ error: "Artist not found" });

    res.json({ message: "Artist deleted", deleted });
  } catch (err) {
    console.error("Error deleting artist:", err);
    res.status(500).json({ error: "Server error deleting artist" });
  }
}
