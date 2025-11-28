// db.mjs
import mongoose from "mongoose";
import "dotenv/config";

const MONGO_URL =
  process.env.MONGO_URL || "mongodb://127.0.0.1:27017/music_insights";

mongoose.set("strictQuery", true);

export async function connectToDatabase() {
  try {
    await mongoose.connect(MONGO_URL);  // ← NO OPTIONS
    console.log("MongoDB connected:", MONGO_URL);
  } catch (err) {
    console.error("MongoDB connection error:", err);
    process.exit(1);
  }
}
