// app.mjs
import "dotenv/config";
import express from "express";
import session from "express-session";
import MongoStore from "connect-mongo";
import morgan from "morgan";

import { connectToDatabase } from "./db.mjs";

// Import routes
import artistRoutes from "./routes/artists.js";
import songRoutes from "./routes/songs.js";
import apiRoutes from "./routes/api.js";
import cors from "cors";



const app = express();

// ----- Database -----
await connectToDatabase();

// ----- Middleware -----
app.use(morgan("dev"));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use(
  cors({
    origin: "https://music-insights-frontend.onrender.com" ,
    credentials: true,
  })
);


// Sessions (for authentication)
app.use(
  session({
    secret: process.env.SESSION_SECRET || "dev-secret",
    resave: false,
    saveUninitialized: false,
    store: MongoStore.create({
      mongoUrl: process.env.MONGO_URL || "mongodb://127.0.0.1:27017/music_insights",
    }),
    cookie: {
      httpOnly: true,
      secure: false, // set to true if using https
    },
  })
);

// Simple auth middleware (placeholder)
function requireAuth(req, res, next) {
  if (!req.session.userId) return res.status(401).json({ error: "Login required" });
  next();
}

// ----- Routes -----
app.get("/", (req, res) => {
  res.send("Music Analytics & Insights API backend is running.");
});

// REST-style organization
app.use("/artists", artistRoutes);
app.use("/songs", songRoutes);
app.use("/api", apiRoutes);

// Protected pages (Next.js will fetch these via API or serve pages)
app.get("/database", requireAuth, (req, res) => {
  res.send("Database analytics placeholder (Next.js will render UI).");
});

app.get("/graph", requireAuth, (req, res) => {
  res.send("Graph visualization placeholder (Next.js will render UI).");
});

// ----- Start server -----
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Backend server running at http://localhost:${PORT}`);
});
