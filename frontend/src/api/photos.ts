import { apiGet } from "./client";

export interface PublicPhoto {
  id: string;
  display_url: string | null;
  mobile_url: string | null;
  thumbnail_url: string | null;
  location: { lat: number; lng: number };
  heading: number | null;
  captured_at: string | null;
  contributor: { display_name: string };
}

export interface PhotoNeighbor {
  id: string;
  thumbnail_url: string | null;
  distance: number;
  bearing: number | null;
}

export interface PhotoNeighbors {
  forward: PhotoNeighbor | null;
  backward: PhotoNeighbor | null;
  nearby: PhotoNeighbor[];
}

export function getPublicPhoto(photoId: string): Promise<PublicPhoto> {
  return apiGet<PublicPhoto>(`/photos/${encodeURIComponent(photoId)}`);
}

export function getPhotoNeighbors(
  photoId: string,
  bearing?: number,
): Promise<PhotoNeighbors> {
  const query =
    bearing === undefined ? "" : `?bearing=${encodeURIComponent(bearing)}`;
  return apiGet<PhotoNeighbors>(
    `/photos/${encodeURIComponent(photoId)}/neighbors${query}`,
  );
}
