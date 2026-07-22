declare module "*.svg" {
  const content: string;
  export default content;
}

declare module "*.png" {
  const content: string;
  export default content;
}

declare module "*.jpg" {
  const content: string;
  export default content;
}

export type PlayerInfo = {
  busName: string;
  identity: string;
};

export type TrackMetadata = {
  title?: string;
  artist?: string;
  album?: string;
  artUrl?: string;
  length?: number;
  trackid?: string;
  url?: string;
};

export type PlayerStatus = {
  available: boolean;
  hasTrack?: boolean;
  player: string;
  identity: string;
  playbackStatus: string;
  position: number;
  volume: number;
  canSeek: boolean;
  canControlVolume: boolean;
  metadata: TrackMetadata;
  error: string;
};

export type PollSnapshot = {
  players: PlayerInfo[];
  status: PlayerStatus;
};
