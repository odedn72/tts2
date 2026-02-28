// Stub: Audio types - to be implemented by developer

export type GenerationStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "failed";

export interface WordTiming {
  word: string;
  start_ms: number;
  end_ms: number;
  start_char: number;
  end_char: number;
}

export interface SentenceTiming {
  sentence: string;
  start_ms: number;
  end_ms: number;
  start_char: number;
  end_char: number;
}

export interface TimingData {
  timing_type: "word" | "sentence";
  words: WordTiming[] | null;
  sentences: SentenceTiming[] | null;
}

export interface AudioMetadata {
  job_id: string;
  duration_ms: number;
  format: string;
  size_bytes: number;
  timing: TimingData;
}
