import { lazy, Suspense, useEffect, useState } from "react";
import {
  get,
  readSelection,
  writeSelection,
  type Metadata,
  type Page,
  type Radius,
  type School,
  type SchoolSummary,
} from "./api";
const MapView = lazy(() => import("./MapView"));

function Failure({ message, retry }: { message: string; retry: () => void }) {
  return (
    <div className="failure" role="alert">
      <p>{message}</p>
      <button onClick={retry}>Try again</button>
    </div>
  );
}

export default function App() {
  const [selection, setSelection] = useState(readSelection);
  const [schools, setSchools] = useState<SchoolSummary[]>([]);
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [school, setSchool] = useState<School | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [detailAttempt, setDetailAttempt] = useState(0);
  const [shareMessage, setShareMessage] = useState("");
  const { schoolId, radius } = selection;

  useEffect(() => {
    const update = () => {
      setSelection(readSelection());
      setShareMessage("");
    };
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    void (async () => {
      const [meta, first] = await Promise.all([
        get<Metadata>("/datasets/current", controller.signal),
        get<Page<SchoolSummary>>("/schools", controller.signal),
      ]);
      const all = [...first.items];
      while (all.length < first.total) {
        const next = await get<Page<SchoolSummary>>(
          `/schools?offset=${all.length}`,
          controller.signal,
        );
        if (!next.items.length)
          throw new Error("The school list changed. Please try again.");
        all.push(...next.items);
      }
      if (!controller.signal.aborted) {
        setSchools(all);
        setMetadata(meta);
      }
    })()
      .catch((err) => {
        if (!controller.signal.aborted)
          setError(
            err instanceof Error ? err.message : "Unable to load school data.",
          );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [attempt]);

  useEffect(() => {
    setSchool(null);
    setDetailError("");
    if (!schoolId) {
      setDetailLoading(false);
      return;
    }
    const controller = new AbortController();
    setDetailLoading(true);
    get<School>(`/schools/${encodeURIComponent(schoolId)}`, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setSchool(data);
      })
      .catch((err) => {
        if (!controller.signal.aborted)
          setDetailError(
            err instanceof Error ? err.message : "Unable to load this school.",
          );
      })
      .finally(() => {
        if (!controller.signal.aborted) setDetailLoading(false);
      });
    return () => controller.abort();
  }, [schoolId, detailAttempt]);

  function select(id: string, nextRadius = radius) {
    writeSelection(id, nextRadius);
    setSelection({ schoolId: id, radius: nextRadius });
    setShareMessage("");
  }
  async function share() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setShareMessage("Link copied");
    } catch {
      setShareMessage("Copy the page address to share this school and radius.");
    }
  }
  const filtered = schools.filter((s) =>
    s.name.toLowerCase().includes(query.trim().toLowerCase()),
  );
  const sourceDate = metadata
    ? new Intl.DateTimeFormat("en-CA", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "UTC",
      }).format(new Date(metadata.retrieved_at_utc))
    : "";
  const refreshDelayed = metadata?.refresh_interval_hours != null &&
    Date.now() - Date.parse(metadata.retrieved_at_utc) > 24 * 60 * 60 * 1000;

  return (
    <>
      <a className="skip-link" href="#school-search">
        Skip to school search
      </a>
      <header className="site-header">
        <a className="brand" href="/">
          <span className="brand-mark" aria-hidden="true">
            b.
          </span>
          <span>
            Burnaby<span className="brand-sub">INFRASTRUCTURE EXPLORER</span>
          </span>
        </a>
        <a className="method-link" href="#about-data">
          About the data <span aria-hidden="true">↗</span>
        </a>
      </header>
      <main>
        <section className="intro">
          <div>
            <p className="eyebrow">
              A CLOSER LOOK AT OUR SCHOOL NEIGHBOURHOODS
            </p>
            <h1>What’s around your school?</h1>
            <p>
              Explore the traffic-calming infrastructure recorded near Burnaby
              schools.
            </p>
          </div>
          <div className="snapshot-label">
            <span className="live-dot" />
            LAST SYNCED FROM CITY DATA
            <strong>{sourceDate ? `${sourceDate} UTC` : "Loading source date…"}</strong>
            {metadata?.refresh_interval_hours && <span>Checks every {metadata.refresh_interval_hours} hours</span>}
          </div>
        </section>
        {refreshDelayed && <p className="freshness-warning" role="status">
          Data refresh is delayed. Showing the last validated download; check the official sources below for newer records.
        </p>}
        <p className="context-note">
          <span aria-hidden="true">ⓘ</span> A radius measures straight-line
          distance from a school point. Recorded coverage is not a measure of
          school safety.
        </p>
        <div className="explorer">
          <aside className="school-panel" aria-label="Find a school">
            <div className="search-block">
              <label htmlFor="school-search">Find your school</label>
              <input
                id="school-search"
                type="search"
                placeholder="Search by school name…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <p className="list-count" role="status">
                {loading
                  ? "Loading schools…"
                  : `${filtered.length} of ${schools.length} schools`}
              </p>
            </div>
            <div className="school-results">
              {error ? (
                <Failure
                  message={error}
                  retry={() => setAttempt((v) => v + 1)}
                />
              ) : (
                <ul className="school-list">
                  {filtered.map((s) => (
                    <li key={s.id}>
                      <button
                        aria-pressed={schoolId === s.id}
                        onClick={() => select(s.id)}
                      >
                        <span className="list-symbol" aria-hidden="true">
                          ⌖
                        </span>
                        <span>{s.name}</span>
                        <span className="list-arrow" aria-hidden="true">
                          ↗
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              {!loading && !error && !filtered.length && (
                <div className="empty">
                  <strong>No schools found</strong>
                  <p>Try a shorter name or clear your search.</p>
                  <button onClick={() => setQuery("")}>Clear search</button>
                </div>
              )}
            </div>
            <div className="list-footer">
              {metadata?.school_count ?? "—"} school locations · City of Burnaby
            </div>
          </aside>
          <Suspense
            fallback={
              <div className="map-panel empty" role="status">
                Loading map…
              </div>
            }
          >
            <MapView
              schools={schools}
              school={school}
              radius={radius}
              onSelect={(id) => select(id)}
            />
          </Suspense>
          <section
            className="detail-panel"
            aria-label="Selected school details"
            aria-busy={detailLoading}
          >
            <p className="eyebrow">SCHOOL SNAPSHOT</p>
            {detailLoading ? (
              <p role="status">Loading school details…</p>
            ) : detailError ? (
              <Failure
                message={detailError}
                retry={() => setDetailAttempt((v) => v + 1)}
              />
            ) : school ? (
              <>
                <h2>{school.name}</h2>
                <p className="detail-location">
                  Burnaby, BC <span>·</span> Source ID {school.source_id}
                </p>
                <fieldset className="radius-picker">
                  <legend>Explore a straight-line radius</legend>
                  {([100, 250, 500] as Radius[]).map((r) => (
                    <label key={r} className={r === radius ? "checked" : ""}>
                      <input
                        type="radio"
                        name="radius"
                        value={r}
                        checked={r === radius}
                        onChange={() => select(schoolId, r)}
                      />
                      {r} m
                    </label>
                  ))}
                </fieldset>
                <div className="count-card">
                  <span className="metric-value">
                    {school.counts[`radius_${radius}_m`]}
                  </span>
                  <strong>recorded features within {radius} m</strong>
                  <p>
                    Traffic-calming records, including removed and unknown
                    statuses.
                  </p>
                </div>
                <h3>Nearest recorded infrastructure</h3>
                <dl className="nearest-list">
                  {[
                    ["Traffic calming", school.nearest_calming],
                    ["Traffic signal", school.nearest_signal],
                    ["Intersection", school.nearest_intersection],
                  ].map(([label, value]) => {
                    const nearest = value as School["nearest_calming"];
                    return (
                      <div key={String(label)}>
                        <dt>
                          {String(label)}
                          <small>
                            {nearest.feature.type === "signal"
                              ? "Excludes removed signals"
                              : nearest.feature.type === "intersection"
                                ? nearest.feature.description
                                : nearest.feature.type}
                          </small>
                        </dt>
                        <dd>
                          {nearest.distance_m.toFixed(1)} <span>m</span>
                        </dd>
                      </div>
                    );
                  })}
                </dl>
                <p className="metric-note">
                  Distances are straight-line measurements, not walking routes.
                </p>
                <button className="share-button" onClick={share}>
                  Copy link to this school <span aria-hidden="true">↗</span>
                </button>
                <p className="share-status" role="status">
                  {shareMessage}
                </p>
                <p className="version">
                  Snapshot {sourceDate}
                  <br />
                  {school.dataset_version}
                </p>
              </>
            ) : (
              <div className="choose-school">
                <span aria-hidden="true">⌖</span>
                <h2>A school is a good place to start.</h2>
                <p>
                  Choose a school from the list or a blue point on the map to
                  explore nearby records.
                </p>
                <p>
                  You can use the list and all school details even if the map is
                  unavailable.
                </p>
              </div>
            )}
          </section>
        </div>
        <section id="about-data" className="about-data">
          <div>
            <p className="eyebrow">READING THE MAP</p>
            <h2>
              Infrastructure records.
              <br />
              With context.
            </h2>
          </div>
          <div>
            <h3>What does coverage mean?</h3>
            <p>
              We count City records within 100, 250, or 500 metres of a school
              point. Measurements use a local projected coordinate system
              (EPSG:26910); the map uses longitude and latitude.
            </p>
            <p>
              This snapshot includes all traffic-calming records, including
              removed and unknown statuses. It does not establish current
              conditions, walking distance, or whether a school is safe. Signal
              distances exclude records marked removed.
            </p>
          </div>
          <div>
            <h3>Source &amp; snapshot</h3>
            <p>
              City of Burnaby open data, last downloaded {sourceDate || "…"} UTC.
              We check every {metadata?.refresh_interval_hours ?? 6} hours and publish after validation.
              This is our download time; the City may update its records on a different schedule. School
              locations are points in the Places of Interest layer, not school
              entrances or property boundaries.
            </p>
            <ul>
              {metadata?.sources.map((source) => (
                <li key={source.name}>
                  <a href={source.source_url} target="_blank" rel="noreferrer">
                    {source.name.replaceAll("_", " ")} ↗
                  </a>
                </li>
              ))}
            </ul>
            <p className="version">
              Dataset {metadata?.dataset_version ?? "loading"}
            </p>
          </div>
        </section>
      </main>
      <footer className="site-footer">
        <span>Burnaby School Infrastructure Explorer</span>
        <span>Public records. Transparent methods.</span>
      </footer>
    </>
  );
}
