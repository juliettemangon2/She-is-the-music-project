// services/spotify.js
import "dotenv/config";

const SPOTIFY_CLIENT_ID = process.env.SPOTIFY_CLIENT_ID;
const SPOTIFY_CLIENT_SECRET = process.env.SPOTIFY_CLIENT_SECRET;

const TOKEN_URL = "https://accounts.spotify.com/api/token";
const SEARCH_URL = "https://api.spotify.com/v1/search";
const ARTIST_URL = "https://api.spotify.com/v1/artists";
const ALBUM_URL = "https://api.spotify.com/v1/albums";

async function getSpotifyToken() {
  if (!SPOTIFY_CLIENT_ID || !SPOTIFY_CLIENT_SECRET) {
    console.error("Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET in env");
    return null;
  }

  const basicAuth = Buffer.from(
    `${SPOTIFY_CLIENT_ID}:${SPOTIFY_CLIENT_SECRET}`
  ).toString("base64");

  try {
    const resp = await fetch(TOKEN_URL, {
      method: "POST",
      headers: {
        Authorization: `Basic ${basicAuth}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({ grant_type: "client_credentials" }),
    });

    if (!resp.ok) {
      console.error("Spotify token error:", resp.status, await resp.text());
      return null;
    }

    const data = await resp.json();
    return data.access_token;
  } catch (err) {
    console.error("Error fetching Spotify token:", err);
    return null;
  }
}

export async function getSpotifyMetadata(artist, title) {
  const token = await getSpotifyToken();
  if (!token) return {};

  const headers = { Authorization: `Bearer ${token}` };

  // Step 1: Search for the track
  const query = `track:"${title}" artist:"${artist}"`;
  const searchParams = new URLSearchParams({
    q: query,
    type: "track",
    limit: "1",
  });

  try {
    const searchResp = await fetch(`${SEARCH_URL}?${searchParams.toString()}`, {
      headers,
    });

    if (!searchResp.ok) {
      console.error(
        "Spotify search error:",
        searchResp.status,
        await searchResp.text()
      );
      return {};
    }

    const searchData = await searchResp.json();
    const items = searchData?.tracks?.items || [];
    if (!items.length) return {};

    const track = items[0];
    const album = track.album || {};
    const albumId = album.id;

    // Step 2: Album details
    let albumLabel = null;
    let copyrightsRaw = [];

    if (albumId) {
      const albumResp = await fetch(`${ALBUM_URL}/${albumId}`, { headers });
      if (albumResp.ok) {
        const albumData = await albumResp.json();
        albumLabel = albumData.label || null;
        copyrightsRaw = albumData.copyrights || [];
      }
    }

    // Release date
    const releaseDate = album.release_date || "";
    const releasePrecision = album.release_date_precision || "";
    const releaseYear = releaseDate ? parseInt(releaseDate.split("-")[0], 10) : null;

    // Step 3: Artist details
    let artistData = {};
    if (Array.isArray(track.artists) && track.artists.length > 0) {
      const artistId = track.artists[0].id;
      if (artistId) {
        const artistResp = await fetch(`${ARTIST_URL}/${artistId}`, { headers });
        if (artistResp.ok) {
          const artistInfo = await artistResp.json();
          artistData = {
            name: artistInfo.name,
            followers: artistInfo.followers?.total,
            popularity: artistInfo.popularity,
            genres: artistInfo.genres || [],
          };
        }
      }
    }

    // Step 4: Track info
    const isrc = track.external_ids?.isrc || null;
    const trackPopularity = track.popularity ?? null;

    // Step 5: Copyright structuring
    const copyrightComposition = copyrightsRaw
      .filter((c) => c.type === "C")
      .map((c) => c.text);

    const copyrightSoundRecording = copyrightsRaw
      .filter((c) => c.type === "P")
      .map((c) => c.text);

    return {
      spotify_id: track.id,
      name: track.name,
      isrc,
      track_popularity: trackPopularity,
      artist: artistData.name || artist,
      artist_followers: artistData.followers,
      artist_popularity: artistData.popularity,
      artist_genres: artistData.genres,
      album_name: album.name,
      label: albumLabel,
      release_date: releaseDate,
      release_date_precision: releasePrecision,
      release_year: releaseYear,
      copyrights: copyrightsRaw,
      copyright_composition: copyrightComposition,
      copyright_sound_recording: copyrightSoundRecording,
    };
  } catch (err) {
    console.error("Error in getSpotifyMetadata:", err);
    return {};
  }
}
