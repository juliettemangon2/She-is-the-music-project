import { Router } from "express";
import {
  listArtists,
  createArtist,
  getArtist,
  deleteArtist,
} from "../controllers/artistsController.js";

const router = Router();

// /artists
router.get("/", listArtists);
router.post("/", createArtist);

// /artists/:id
router.get("/:id", getArtist);
router.delete("/:id", deleteArtist);

export default router;
