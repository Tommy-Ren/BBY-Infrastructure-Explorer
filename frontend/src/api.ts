import type { Polygon } from "geojson";

export type Radius = 100 | 250 | 500;
export type Location = { longitude: number; latitude: number };
export type SchoolSummary = {
  id: string;
  source_id: number;
  name: string;
  location: Location;
};
export type Infrastructure = {
  id: string;
  source_id: number;
  type: string;
  location: Location;
  description: string | null;
  service_status: string | null;
};
export type Nearest = { feature: Infrastructure; distance_m: number };
export type School = SchoolSummary & {
  dataset_version: string;
  counts: Record<`radius_${Radius}_m`, number>;
  nearest_calming: Nearest;
  nearest_signal: Nearest;
  nearest_intersection: Nearest;
  radius_geometry: Record<string, Polygon>;
};
export type Metadata = {
  dataset_version: string;
  retrieved_at_utc: string;
  school_count: number;
  feature_count: number;
  coverage_rule: string;
  limitation: string;
  sources: { name: string; source_url: string; source_count: number }[];
};
export type Page<T> = {
  items: T[];
  total: number;
  offset: number;
  limit: number;
  dataset_version: string;
};
const base = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export async function get<T>(path: string, signal: AbortSignal): Promise<T> {
  const timeout = AbortSignal.timeout(15000);
  const response = await fetch(`${base}/api/v1${path}`, {
    signal: AbortSignal.any([signal, timeout]),
  });
  if (!response.ok) {
    throw new Error(
      response.status === 404
        ? "This school is not in the current dataset. Choose a school from the list."
        : "The data service could not complete this request. Please try again.",
    );
  }
  return response.json();
}

export function readSelection() {
  const params = new URLSearchParams(window.location.search);
  const radius = Number(params.get("radius"));
  return {
    schoolId: params.get("school") ?? "",
    radius: ([100, 250, 500].includes(radius) ? radius : 250) as Radius,
  };
}

export function writeSelection(schoolId: string, radius: Radius) {
  const url = new URL(window.location.href);
  if (schoolId) url.searchParams.set("school", schoolId);
  else url.searchParams.delete("school");
  url.searchParams.set("radius", String(radius));
  window.history.pushState({}, "", url);
}
