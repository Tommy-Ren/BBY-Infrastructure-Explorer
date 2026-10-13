import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import type { GeoJSONSource, Map as LibreMap } from "maplibre-gl";
import type { FeatureCollection, Geometry } from "geojson";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import {
  get,
  type Infrastructure,
  type Page,
  type Radius,
  type School,
  type SchoolSummary,
} from "./api";

const empty: FeatureCollection = { type: "FeatureCollection", features: [] };
maplibregl.setWorkerUrl(workerUrl);
const points = (
  rows: (SchoolSummary | Infrastructure)[],
): FeatureCollection => ({
  type: "FeatureCollection",
  features: rows.map((row) => ({
    type: "Feature",
    properties: { id: row.id, label: "name" in row ? row.name : row.type },
    geometry: {
      type: "Point",
      coordinates: [row.location.longitude, row.location.latitude],
    },
  })),
});

export default function MapView({
  schools,
  school,
  radius,
  onSelect,
}: {
  schools: SchoolSummary[];
  school: School | null;
  radius: Radius;
  onSelect: (id: string) => void;
}) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LibreMap | null>(null);
  const callback = useRef(onSelect);
  callback.current = onSelect;
  const [ready, setReady] = useState(false);
  const [mapError, setMapError] = useState("");
  const [featureError, setFeatureError] = useState("");
  const [loadingFeatures, setLoadingFeatures] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!container.current) return;
    let map: LibreMap;
    try {
      map = new maplibregl.Map({
        container: container.current,
        center: [-122.96, 49.25],
        zoom: 11.2,
        style: {
          version: 8,
          sources: {
            basemap: {
              type: "raster",
              tileSize: 256,
              tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
              attribution:
                '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
              maxzoom: 19,
            },
          },
          layers: [{ id: "basemap", type: "raster", source: "basemap" }],
        },
      });
      mapRef.current = map;
      map.addControl(
        new maplibregl.NavigationControl({ showCompass: false }),
        "top-right",
      );
      map.addControl(new maplibregl.ScaleControl({ unit: "metric" }));
      map.on("error", () =>
        setMapError(
          "Some map tiles could not load. School data and the list remain available.",
        ),
      );
      map.on("load", () => {
        for (const id of ["schools", "features", "radius", "selected"])
          map.addSource(id, { type: "geojson", data: empty });
        map.addLayer({
          id: "radius-fill",
          type: "fill",
          source: "radius",
          paint: { "fill-color": "#228369", "fill-opacity": 0.12 },
        });
        map.addLayer({
          id: "radius-line",
          type: "line",
          source: "radius",
          paint: {
            "line-color": "#16715b",
            "line-width": 2,
            "line-dasharray": [3, 2],
          },
        });
        map.addLayer({
          id: "features",
          type: "circle",
          source: "features",
          paint: {
            "circle-radius": 4,
            "circle-color": "#b85e23",
            "circle-stroke-width": 1.5,
            "circle-stroke-color": "#fff",
          },
        });
        map.addLayer({
          id: "schools",
          type: "circle",
          source: "schools",
          paint: {
            "circle-radius": 6,
            "circle-color": "#204b62",
            "circle-stroke-width": 2,
            "circle-stroke-color": "#fff",
          },
        });
        map.addLayer({
          id: "selected",
          type: "circle",
          source: "selected",
          paint: {
            "circle-radius": 9,
            "circle-color": "#163e36",
            "circle-stroke-width": 3,
            "circle-stroke-color": "#fff",
          },
        });
        map.on("click", "schools", (event) => {
          const id = event.features?.[0]?.properties?.id;
          if (typeof id === "string") callback.current(id);
        });
        map.on("click", "features", (event) => {
          const feature = event.features?.[0];
          if (feature?.geometry.type === "Point")
            new maplibregl.Popup()
              .setLngLat(feature.geometry.coordinates as [number, number])
              .setText(String(feature.properties?.label ?? "Recorded feature"))
              .addTo(map);
        });
        map.on("mouseenter", "schools", () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", "schools", () => {
          map.getCanvas().style.cursor = "";
        });
        setReady(true);
      });
    } catch {
      setMapError(
        "The map is unavailable in this browser. Explore every school using the list and details.",
      );
      return;
    }
    const resize = new ResizeObserver(() => map.resize());
    resize.observe(container.current);
    return () => {
      resize.disconnect();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (ready)
      (mapRef.current?.getSource("schools") as GeoJSONSource).setData(
        points(schools),
      );
  }, [ready, schools]);

  useEffect(() => {
    if (!ready || !mapRef.current) return;
    const map = mapRef.current;
    (map.getSource("selected") as GeoJSONSource).setData(
      school ? points([school]) : empty,
    );
    const geometry: Geometry | undefined =
      school?.radius_geometry[String(radius)];
    (map.getSource("radius") as GeoJSONSource).setData(
      geometry
        ? {
            type: "FeatureCollection",
            features: [{ type: "Feature", properties: {}, geometry }],
          }
        : empty,
    );
    if (school && geometry?.type === "Polygon") {
      const bounds = new maplibregl.LngLatBounds();
      geometry.coordinates[0].forEach((p) =>
        bounds.extend(p as [number, number]),
      );
      map.fitBounds(bounds, { padding: 60, maxZoom: 16, duration: 0 });
    }
  }, [ready, school, radius]);

  useEffect(() => {
    if (!ready || !mapRef.current) return;
    const map = mapRef.current;
    let controller: AbortController | undefined;
    let disposed = false;
    const load = async () => {
      controller?.abort();
      controller = new AbortController();
      const signal = controller.signal;
      const bounds = map.getBounds();
      (map.getSource("features") as GeoJSONSource).setData(empty);
      if (
        bounds.getEast() - bounds.getWest() > 0.1 ||
        bounds.getNorth() - bounds.getSouth() > 0.1
      ) {
        setLoadingFeatures(false);
        setFeatureError("Select a school or zoom in to see recorded features.");
        return;
      }
      setLoadingFeatures(true);
      setFeatureError("");
      try {
        const bbox = [
          bounds.getWest(),
          bounds.getSouth(),
          bounds.getEast(),
          bounds.getNorth(),
        ].join(",");
        const records: Infrastructure[] = [];
        let total = 1;
        while (records.length < total) {
          const page = await get<Page<Infrastructure>>(
            `/features?bbox=${bbox}&offset=${records.length}`,
            signal,
          );
          records.push(...page.items);
          total = page.total;
          if (!page.items.length) break;
        }
        if (!signal.aborted && !disposed)
          (map.getSource("features") as GeoJSONSource).setData(points(records));
      } catch {
        if (!signal.aborted && !disposed)
          setFeatureError(
            "Nearby features could not load. Try loading them again.",
          );
      } finally {
        if (!signal.aborted && !disposed) setLoadingFeatures(false);
      }
    };
    map.on("moveend", load);
    void load();
    return () => {
      disposed = true;
      controller?.abort();
      map.off("moveend", load);
    };
  }, [ready, attempt]);

  return (
    <section className="map-panel" aria-label="School infrastructure map">
      <div
        ref={container}
        className="map-canvas"
        aria-label="Interactive map; schools are also available in the list"
      />
      <div className="map-heading">
        <span className="eyebrow">THE NEIGHBOURHOOD VIEW</span>
        <strong>{school ? school.name : "Burnaby, British Columbia"}</strong>
      </div>
      <div className="map-legend">
        <span>
          <i className="dot school-dot" />
          School
        </span>
        <span>
          <i className="dot feature-dot" />
          Recorded feature
        </span>
        <span>
          <i className="radius-swatch" />
          {radius} m radius
        </span>
      </div>
      {(mapError || featureError || loadingFeatures) && (
        <div className="map-notice" role="status">
          {mapError || featureError || "Loading nearby features…"}
          {featureError.includes("could not load") && (
            <button onClick={() => setAttempt((v) => v + 1)}>
              Retry features
            </button>
          )}
        </div>
      )}
    </section>
  );
}
