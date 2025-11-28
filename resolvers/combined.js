// resolvers/combined.js
import { getAllDerivativesFromSHS } from "../services/shs.js";
import { getDiscogsMetadata } from "../services/discogs.js";

// -------------------------------------
// Helper: Enrich Discogs versions with missing artist names
// -------------------------------------
async function enrichDiscogsVersionsWithArtist(versions) {
  if (!versions || !Array.isArray(versions)) return [];

  const enriched = [];

  for (const version of versions) {
    let enrichedVersion = { ...version };

    if (!enrichedVersion.artist && enrichedVersion.uri) {
      try {
        const releaseId = enrichedVersion.uri.split("/").pop();
        const resp = await fetch(`https://api.discogs.com/releases/${releaseId}`, {
          headers: { "User-Agent": "SITMApp/0.1" },
        });

        if (resp.ok) {
          const releaseJson = await resp.json();
          const artists = releaseJson.artists || [];
          const artistName = artists.map((a) => a.name).join(" & ");
          enrichedVersion.artist = artistName || null;
        }
      } catch (err) {
        console.error("Error enriching Discogs version artist:", err);
      }

      // Avoid rate-limiting
      await new Promise((res) => setTimeout(res, 1000));
    }

    enriched.push(enrichedVersion);
  }

  return enriched;
}

// -------------------------------------
// MAIN FUNCTION: resolveCombinedDerivatives
// -------------------------------------
export async function resolveCombinedDerivatives(artist, title) {
  const combined = {
    secondhandsongs: [],
    discogs_master: null,
  };

  // 1. SecondHandSongs
  try {
    const shsResults = await getAllDerivativesFromSHS(artist, title);
    combined.secondhandsongs = shsResults || [];
  } catch (err) {
    console.error("SHS error:", err);
  }

  // 2. Discogs master data
  try {
    const discogsData = await getDiscogsMetadata(artist, title);

    if (discogsData?.versions) {
      discogsData.versions = await enrichDiscogsVersionsWithArtist(
        discogsData.versions
      );
    }

    combined.discogs_master = discogsData || null;
  } catch (err) {
    console.error("Discogs master error:", err);
  }

  return combined;
}
