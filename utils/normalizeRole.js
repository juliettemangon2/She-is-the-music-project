// utils/normalizeRole.js

// Port of Python normalize_role(role: str) -> str | None
// - lowercases
// - matches substrings like "lyrics", "composer", etc.
// - maps to canonical role names
// - otherwise capitalizes the string

const ROLE_REPLACEMENTS = {
  lyrics: "Lyricist",
  composer: "Composer",
  written: "Composer",
  producer: "Producer",
  engineer: "Engineer",
  vocals: "Vocalist",
  guitar: "Guitar",
};

export function normalizeRole(role) {
  if (!role) return null;

  const lower = String(role).toLowerCase();

  for (const [key, value] of Object.entries(ROLE_REPLACEMENTS)) {
    if (lower.includes(key)) {
      return value;
    }
  }

  // Fallback: basic capitalization
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}
