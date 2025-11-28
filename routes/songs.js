import { Router } from "express";
import {
  listSongs,
  createSong,
  getSong,
  deleteSong
} from "../controllers/songsController.js";

const router = Router();

// /songs
router.get("/", listSongs);
router.post("/", createSong);

// /songs/:id
router.get("/:id", getSong);
router.delete("/:id", deleteSong);

export default router;
