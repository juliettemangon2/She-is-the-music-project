// routes/api.js
import { Router } from "express";
import {
  fetchOneSong,
  fetchMultipleSongs,
  getDatabaseWithInsights
} from "../controllers/metadataController.js";

const router = Router();

/**
 * POST /api/fetch-one
 * Fetches metadata AND saves to DB (Option B)
 */
router.post("/fetch-one", async (req, res) => {
  try {
    const { artist, title } = req.body;
    if (!artist || !title) {
      return res.status(400).json({ error: "artist and title required" });
    }

    const result = await fetchOneSong(artist, title);
    res.json(result);
  } catch (err) {
    console.error("Error /api/fetch-one:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

/**
 * POST /api/fetch-multiple
 * Fetches metadata for a list of songs AND saves all to DB
 */
router.post("/fetch-multiple", async (req, res) => {
  try {
    const { songs } = req.body;
    if (!Array.isArray(songs) || songs.length === 0) {
      return res.status(400).json({ error: "songs[] required" });
    }

    const artists = songs.map(s => s.artist);
    const titles = songs.map(s => s.title);

    const result = await fetchMultipleSongs(artists, titles);
    res.json(result);
  } catch (err) {
    console.error("Error /api/fetch-multiple:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

/**
 * GET /api/database
 * Load entire Mongo database with insights
 */
router.get("/database", async (req, res) => {
  try {
    const db = await getDatabaseWithInsights();
    res.json(db);
  } catch (err) {
    console.error("Error /api/database:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

export default router;
