"use client";

import { createContext, useContext, useState, ReactNode } from "react";

// Full song type matching your API response
export type Contributor = {
  name: string;
  roles: string[];
  sources?: string[];
};

export type Song = {
  artist: string;
  title: string;
  album?: string | null;
  release_year?: number | null;
  label?: string | null;
  spotify_popularity?: number;
  artist_popularity?: number;
  genres: string[];
  publishers: string[];
  contributors: Contributor[];
  derivatives?: {
    secondhandsongs?: Array<{
      title: string;
      artist: string;
      relation_type: string;
      uri: string;
    }>;
  };
  flags?: Array<{ type: string; message: string }>;
};

export type SharedItem = {
  name: string;
  count: number;
  songs: string[];
};

export type DerivedInsights = {
  summary?: {
    total_songs: number;
    unique_contributors: number;
    unique_labels: number;
  };
  shared?: {
    contributors: SharedItem[];
    labels: SharedItem[];
    genres: SharedItem[];
    publishers: SharedItem[];
  };
  popularity_distribution?: {
    track: Record<string, string[]>;
    artist: Record<string, string[]>;
  };
  extra_summary?: {
    role_tally: Record<string, number>;
    derivative_count: number;
  };
  clustering?: Array<{ names: string[]; song_count: number }>;
  linking?: Array<{ linker: string; linked: string[] }>;
};

export type ApiResponse = {
  songs: Song[];
  derived_insights: DerivedInsights;
};

type SongContextType = {
  // Current session data (from most recent submission)
  currentData: ApiResponse | null;
  setCurrentData: (data: ApiResponse | null) => void;
  // Loading state
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
};

const SongContext = createContext<SongContextType>({
  currentData: null,
  setCurrentData: () => {},
  isLoading: false,
  setIsLoading: () => {},
});

export function SongProvider({ children }: { children: ReactNode }) {
  const [currentData, setCurrentData] = useState<ApiResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  return (
    <SongContext.Provider
      value={{ currentData, setCurrentData, isLoading, setIsLoading }}
    >
      {children}
    </SongContext.Provider>
  );
}

export function useSongContext() {
  return useContext(SongContext);
}