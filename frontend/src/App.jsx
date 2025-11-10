import React, { useEffect, useMemo, useRef, useState } from "react";

// ============ Speech2Text X — UI v2 ============
// Pestañas: Inicio / Transcribir / Biblioteca / Historial
// Biblioteca: lee /audio/_manifest.json (strings u objetos) y prellena la URL http://files/audio/<nombre>
// Historial: guarda transcripciones finalizadas en localStorage
// Nota: las clases Tailwind son opcionales (sin Tailwind se ve sobrio pero ok)

const API_BASE_DEFAULT = (import.meta?.env?.VITE_API_BASE || "http://localhost:8000").replace(/\/$/, "");

function cx(...xs) { return xs.filter(Boolean).join(" "); }
function prettyMs(ms) { if (ms == null) return ""; const s = Math.floor(ms/1000); const mm = String(Math.floor(s/60)).padStart(2,"0"); const ss = String(s%60).padStart(2,"0"); return `${mm}:${ss}`; }

// -------------------- UI bits --------------------
function Button({children, onClick, variant="primary", className, disabled, type}) {
  const base = "px-4 py-2 rounded-xl font-medium transition text-sm";
  const v = {
    primary: "bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-60",
    ghost:   "bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700",
    subtle:  "bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-800",
    danger:  "bg-rose-600 hover:bg-rose-500 text-white",
  }[variant];
  return <button type={type} disabled={disabled} onClick={onClick} className={cx(base, v, className)}>{children}</button>;
}

function Card({title, subtitle, children, footer, className}) {
  return (
    <div className={cx("rounded-2xl shadow border border-zinc-800 bg-zinc-900/40", className)}>
      {(title || subtitle) && (
        <div className="p-5 border-b border-zinc-800">
          {title && <div className="text-lg font-semibold text-zinc-100">{title}</div>}
          {subtitle && <div className="text-sm text-zinc-400 mt-1">{subtitle}</div>}
        </div>
      )}
      <div className="p-5 text-zinc-200">{children}</div>
      {footer && <div className="p-4 border-t border-zinc-800 text-sm text-zinc-300">{footer}</div>}
    </div>
  );
}

function Field({label, hint, children}) {
  return (
    <label className="block mb-4">
      {label && <div className="text-sm text-zinc-300 mb-1">{label}</div>}
      {children}
      {hint && <div className="text-xs text-zinc-400 mt-1">{hint}</div>}
    </label>
  );
}

function StatusPill({ok, text}) {
  return (
    <span className={cx(
      "inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs",
      ok ? "bg-emerald-900/40 text-emerald-300" : "bg-rose-900/30 text-rose-300"
    )}>{text}</span>
  );
}

function Copy({text}) {
  return <Button variant="subtle" className="text-xs py-1 px-2" onClick={()=>navigator.clipboard.writeText(text)}>Copiar</Button>;
}

// -------------------- Storage helpers --------------------
function useLocalState(key, initial) {
  const [v, setV] = useState(() => {
    try { const s = localStorage.getItem(key); return s ? JSON.parse(s) : initial; } catch { return initial; }
  });
  useEffect(() => { try { localStorage.setItem(key, JSON.stringify(v)); } catch {} }, [key, v]);
  return [v, setV];
}

// -------------------- Main App --------------------
export default function App() {
  const [apiBase, setApiBase] = useLocalState("s2x.apiBase", API_BASE_DEFAULT);
  const [tab, setTab] = useLocalState("s2x.tab", "home");
  const [health, setHealth] = useState(null);
  const [user, setUser] = useLocalState("s2x.user", null);
  const [project, setProject] = useLocalState("s2x.project", null);
  const [history, setHistory] = useLocalState("s2x.history", []); // transcripciones finalizadas

  // Form transcripción
  const [audioUrl, setAudioUrl] = useState("");
  const [languageHint, setLanguageHint] = useState("");
  const [modelName, setModelName] = useState("");
  const [temperature, setTemperature] = useState(0.0);
  const [beam, setBeam] = useState(5);

  // Estado de job
  const [transcription, setTranscription] = useState(null);
  const [segments, setSegments] = useState([]);
  const [isBusy, setIsBusy] = useState(false);
  const pollRef = useRef(null);

  const api = useMemo(() => ({
    async get(p)  { const r = await fetch(`${apiBase}${p}`); if(!r.ok) throw new Error(`GET ${p} ${r.status}`); return r.json(); },
    async post(p, body) {
      const r = await fetch(`${apiBase}${p}`, { method:"POST", headers:{ "Content-Type":"application/json" }, body: JSON.stringify(body ?? {}) });
      const txt = await r.text(); if(!r.ok) throw new Error(`POST ${p} ${r.status}: ${txt}`); return txt ? JSON.parse(txt) : {};
    },
  }), [apiBase]);

  // Health & bootstrap
  useEffect(() => { (async () => { try { setHealth(await fetch(`${apiBase}/health`).then(r=>r.json())); } catch { setHealth(null); } })(); }, [apiBase]);

  useEffect(() => { (async () => {
    if (user && project) return;
    try {
      const u  = await api.post("/users",   { email: `guest+${Date.now()}@example.com`, name:"Invitado", pwd_hash: Math.random().toString(36).slice(2), role:"user" });
      const pr = await api.post("/projects",{ owner_id: u.id, name:"Mis transcripciones" });
      setUser(u); setProject(pr);
    } catch(e) { console.error(e); }
  })(); /* eslint-disable-next-line */ }, []); // intencionalmente sin deps para no re-bootstrapear

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  // -------- Transcribe flow --------
  async function startTranscription() {
    if (!audioUrl) return alert("Pega una URL del audio");
    if (!project)  return alert("Proyecto aún no está listo");
    setIsBusy(true); setSegments([]); setTranscription(null);
    try {
      const audio = await api.post("/audio", { project_id: project.id, s3_uri: audioUrl });
      const t = await api.post("/transcriptions",{
        audio_id: audio.id,
        mode:"batch",
        language_hint: languageHint || null,
        model_name: modelName || null,
        temperature: parseFloat(temperature),
        beam_size: parseInt(beam, 10),
      });
      setTranscription(t);
      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = setInterval(async () => {
        try {
          const cur = await api.get(`/transcriptions/${t.id}`);
          setTranscription(cur);
          if (["succeeded","failed"].includes(cur.status)) {
            clearInterval(pollRef.current); pollRef.current = null; setIsBusy(false);
            if (cur.status === "succeeded") {
              const segs = await api.get(`/segments/${t.id}?limit=2000&offset=0`);
              setSegments(segs || []);
              // guarda en historial (local)
              try {
                setHistory(([{ id: cur.id, created_at: cur.created_at || new Date().toISOString(),
                  language: cur.language_detected, text: cur.text_full, artifacts: cur.artifacts, audio_url: audioUrl }])
                  .concat(history).slice(0,50));
              } catch {}
            }
          }
        } catch (e) { console.error("poll", e); }
      }, 1200);
    } catch(e) {
      setIsBusy(false); console.error(e); alert("Error: " + e.message);
    }
  }

  async function createShare() {
    if (!transcription?.id) return;
    const token = Math.random().toString(36).slice(2);
    try {
      const share = await api.post("/shares", { transcription_id: transcription.id, token, kind:"public", can_edit:false, expires_at:null, created_by: user?.id || null });
      alert(`Enlace: ${window.location.origin}/#/share/${share.token}`);
    } catch(e) { alert("No se pudo crear el enlace: " + e.message); }
  }

  // -------- Biblioteca (manifest) --------
  const [libItems, setLibItems] = useState([]);
  const [libError, setLibError]   = useState("");

  async function loadManifest() {
    setLibError(""); setLibItems([]);
    const candidates = [
      `${window.location.origin}/audio/_manifest.json`,
      `http://localhost:8081/audio/_manifest.json`,
    ];
    for (const url of candidates) {
      try {
        const r = await fetch(url, { cache: "no-store" });
        if (!r.ok) continue;
        const j = await r.json();
        if (Array.isArray(j)) {
          // acepta: ["a.mp3", {"name":"b.mp3","title":"..."}]
          const mapped = j.map((it) => {
            if (typeof it === "string") return { name: it };
            const name = it?.name || it?.file || (typeof it?.path === "string" ? it.path.split("/").pop() : undefined);
            return name ? { name, title: it.title, hint: it.hint } : null;
          }).filter(Boolean);
          if (mapped.length) { setLibItems(mapped); return; }
        }
      } catch { /* try next */ }
    }
    // Fallback
    setLibItems([
      { name: "test_3.mp3",   title: "Ejemplo local (usa files)", hint: "Coloca este archivo en frontend/public/audio/" },
      { name: "sample_es.mp3", title: "Ejemplo 2",               hint: "Copia un archivo con este nombre para probar" },
    ]);
    setLibError("No se encontró /audio/_manifest.json o está vacío. Usa un array de strings u objetos {name, title?}.");
  }

  useEffect(() => { if (tab === "library") loadManifest(); }, [tab]);

  function useThisAudio(name) {
    if (!name) { alert("No se pudo leer el nombre del archivo del manifest"); return; }
    const urlFiles = `http://files/audio/${name}`;
    const urlVite  = `${window.location.origin}/audio/${name}`;
    setAudioUrl(urlFiles); setTab("transcribe");
    alert(`Usando: ${urlFiles}\nSi prefieres Vite: ${urlVite}`);
  }

  // -------------------- Views --------------------
  const HomeView = () => (
    <div className="grid lg:grid-cols-3 gap-4">
      <Card title="Bienvenido a Speech2Text X" subtitle="Sube audios por URL y obtén texto, segmentos y subtítulos">
        <ol className="list-decimal pl-5 space-y-2 text-sm">
          <li>Pon tus audios en <span className="font-mono">frontend/public/audio/</span>.</li>
          <li>(Dev) Levanta el servicio <span className="font-mono">files</span> del compose.</li>
          <li>Ve a <b>Transcribir</b> y pega <span className="font-mono">http://files/audio/&lt;archivo&gt;</span>.</li>
        </ol>
        <div className="mt-4 flex flex-wrap gap-2">
          <StatusPill ok={!!health} text={health ? `API: ${apiBase}` : "API no disponible"} />
          <StatusPill ok={health?.status === "ok"} text={`Health: ${health ? health.status : "?"}${health?.db!=null ? ` (db=${String(health.db)})` : ""}`} />
        </div>
      </Card>

      <Card title="Atajos útiles">
        <div className="space-y-2 text-sm">
          <div>• <b>Idioma (hint)</b>: ayuda a la detección si lo conoces.</div>
          <div>• <b>Modelo</b>: tiny/base/small/medium/large-v3 (dependiendo del backend).</div>
          <div>• <b>Compartir</b>: genera un enlace público (token).</div>
          <div>• <b>Artefactos</b>: descarga SRT/VTT al terminar.</div>
        </div>
        <div className="mt-4">
          <Button onClick={()=>setTab("transcribe")}>Ir a Transcribir</Button>
        </div>
      </Card>

      <Card title="Biblioteca rápida" subtitle="Usa el manifest para listar audios locales">
        <div className="text-sm mb-3">
          Crea <span className="font-mono">frontend/public/audio/_manifest.json</span> con un array.
          Ej: <span className="font-mono">["test_3.mp3","clase1.wav"]</span>
        </div>
        <Button variant="subtle" onClick={loadManifest}>Actualizar lista</Button>
        <ul className="mt-4 space-y-2 text-sm">
          {libItems.map((it,i)=>(
            <li key={i} className="flex items-center justify-between gap-2 border border-zinc-800 rounded-xl p-2">
              <div>
                <div className="font-medium">{it.title || it.name || "(sin nombre)"}</div>
                <div className="text-xs text-zinc-400">{it.name || "-"}</div>
              </div>
              <Button variant="ghost" onClick={()=>useThisAudio(it.name)}>Usar</Button>
            </li>
          ))}
        </ul>
        {libError && <div className="text-xs text-amber-300 mt-3">{libError}</div>}
      </Card>
    </div>
  );

  const TranscribeView = () => (
    <div className="space-y-4">
      <Card title="Configuración rápida">
        <div className="grid md:grid-cols-3 gap-4">
          <Field label="API Base">
            <input className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2" value={apiBase} onChange={e=>setApiBase(e.target.value)} />
          </Field>
          <Field label="Idioma (hint)">
            <select className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2" value={languageHint} onChange={e=>setLanguageHint(e.target.value)}>
              <option value="">Auto</option><option value="es">Español</option><option value="en">English</option><option value="pt">Português</option><option value="fr">Français</option>
            </select>
          </Field>
          <Field label="Modelo (opcional)" hint="tiny/base/small/medium/large-v3; depende del backend">
            <input className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2" value={modelName} onChange={e=>setModelName(e.target.value)} placeholder="base" />
          </Field>
        </div>
        <div className="grid md:grid-cols-2 gap-4 mt-2">
          <Field label={`Temperatura: ${temperature}`}>
            <input type="range" min={0} max={1} step={0.1} value={temperature} onChange={e=>setTemperature(e.target.value)} className="w-full" />
          </Field>
          <Field label={`Beam size: ${beam}`}>
            <input type="range" min={1} max={10} step={1} value={beam} onChange={e=>setBeam(e.target.value)} className="w-full" />
          </Field>
        </div>
      </Card>

      <Card title="1) Ingresa la URL del audio" subtitle="Sugerido en dev: http://files/audio/<archivo>">
        <Field label="URL del audio (http/https)" hint="Ej: http://files/audio/test_3.mp3">
          <input className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2" value={audioUrl} onChange={e=>setAudioUrl(e.target.value)} placeholder="Pega aquí un enlace directo al archivo de audio" />
        </Field>
        <div className="flex items-center gap-3">
          <Button onClick={startTranscription} disabled={isBusy || !audioUrl}>{isBusy ? "Procesando…" : "Transcribir"}</Button>
          {transcription?.status && <span className="text-sm text-zinc-300">Estado actual: <b>{transcription.status}</b></span>}
        </div>
        {/* <div className="text-xs text-zinc-400 mt-3">
          Tip: también puedes usar {window.location.origin.replace(/\/$/,'') + "/audio/<archivo>"} si expones tu dev-server y el contenedor puede verlo.
        </div> */}
      </Card>

      {transcription && (
        <Card title="2) Resultado" footer={
          <div className="flex flex-wrap items-center gap-2">
            {transcription?.artifacts?.srt && <a className="underline text-blue-300" href={transcription.artifacts.srt} target="_blank">Descargar SRT</a>}
            {transcription?.artifacts?.vtt && <a className="underline text-blue-300" href={transcription.artifacts.vtt} target="_blank">Descargar VTT</a>}
            {transcription?.id && <Button variant="ghost" onClick={createShare}>Compartir (público)</Button>}
          </div>
        }>
          {transcription.status === "succeeded" ? (
            <>
              <div className="mb-3 text-sm text-zinc-400">
                Idioma detectado: <b className="text-zinc-200">{transcription.language_detected || "(no disp.)"}</b> · Confianza: {transcription.confidence ?? "-"}
              </div>

              <div className="flex items-center gap-2 mb-2">
                <div className="text-lg font-semibold">Texto completo</div>
                {transcription.text_full && <Copy text={transcription.text_full} />}
              </div>
              <textarea readOnly className="w-full min-h-40 bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-sm" value={transcription.text_full || "(vacío)"} />

              <div className="mt-6">
                <div className="flex items-center gap-2 mb-2">
                  <div className="text-lg font-semibold">Segmentos</div>
                  {segments?.length>0 && <span className="text-xs text-zinc-400">{segments.length} segmentos</span>}
                </div>
                {segments?.length>0 ? (
                  <div className="overflow-x-auto border border-zinc-800 rounded-xl">
                    <table className="w-full text-sm">
                      <thead className="bg-zinc-900/60">
                        <tr className="text-left">
                          <th className="px-3 py-2">#</th>
                          <th className="px-3 py-2">Inicio</th>
                          <th className="px-3 py-2">Fin</th>
                          <th className="px-3 py-2">Texto</th>
                          <th className="px-3 py-2">Hablante</th>
                          <th className="px-3 py-2">Conf.</th>
                        </tr>
                      </thead>
                      <tbody>
                        {segments.map((s,i)=>(
                          <tr key={i} className={i%2 ? "bg-zinc-900/30" : "bg-transparent"}>
                            <td className="px-3 py-2">{i+1}</td>
                            <td className="px-3 py-2 font-mono text-xs">{prettyMs(s.start_ms)}</td>
                            <td className="px-3 py-2 font-mono text-xs">{prettyMs(s.end_ms)}</td>
                            <td className="px-3 py-2">{s.text}</td>
                            <td className="px-3 py-2">{s.speaker_label || "-"}</td>
                            <td className="px-3 py-2">{s.confidence == null ? "-" : s.confidence}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-sm text-zinc-400">No hay segmentos (aún).</div>
                )}
              </div>
            </>
          ) : (
            <div className="text-sm text-zinc-300">Estado: {transcription.status}. {isBusy ? "Procesando en background, actualizando…" : null}</div>
          )}
        </Card>
      )}
    </div>
  );

  const LibraryView = () => (
    <div className="space-y-4">
      <Card title="Audios locales (manifest)" subtitle="Se busca /audio/_manifest.json. Click en 'Actualizar lista' para leerlo.">
        <div className="flex items-center gap-2">
          <Button variant="subtle" onClick={loadManifest}>Actualizar lista</Button>
          <Button variant="ghost" onClick={()=>window.open("/audio/_manifest.json", "_blank")}>Abrir manifest</Button>
        </div>
        <ul className="mt-4 grid md:grid-cols-2 gap-3">
          {libItems.map((it,i)=>(
            <li key={i} className="border border-zinc-800 rounded-xl p-3">
              <div className="font-medium">{it.title || it.name}</div>
              <div className="text-xs text-zinc-400">{it.name}</div>
              <div className="mt-2 flex items-center gap-2">
                <Button onClick={()=>useThisAudio(it.name)}>Usar</Button>
                <a className="text-blue-300 underline text-sm" href={`/audio/${it.name}`} target="_blank">Ver</a>
              </div>
            </li>
          ))}
        </ul>
        {libError && <div className="text-xs text-amber-300 mt-3">{libError}</div>}
        <div className="text-xs text-zinc-400 mt-4">Formato del manifest: <span className="font-mono">["archivo1.mp3","archivo2.wav"]</span></div>
      </Card>
    </div>
  );

  const HistoryView = () => (
    <div className="space-y-4">
      <Card title="Transcripciones recientes" subtitle="Guardadas localmente en este navegador">
        {history.length===0 ? (
          <div className="text-sm text-zinc-400">Aún no hay transcripciones completadas en esta sesión.</div>
        ) : (
          <div className="overflow-x-auto border border-zinc-800 rounded-xl">
            <table className="w-full text-sm">
              <thead className="bg-zinc-900/60">
                <tr className="text-left">
                  <th className="px-3 py-2">Fecha</th>
                  <th className="px-3 py-2">Idioma</th>
                  <th className="px-3 py-2">Extracto</th>
                  <th className="px-3 py-2">Artefactos</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h,i)=>(
                  <tr key={i} className={i%2 ? "bg-zinc-900/30" : "bg-transparent"}>
                    <td className="px-3 py-2">{new Date(h.created_at).toLocaleString()}</td>
                    <td className="px-3 py-2">{h.language || "-"}</td>
                    <td className="px-3 py-2 truncate max-w-[36ch]">{h.text?.slice(0,140) || "(sin texto)"}</td>
                    <td className="px-3 py-2 space-x-3">
                      {h.artifacts?.srt && <a className="underline text-blue-300" href={h.artifacts.srt} target="_blank">SRT</a>}
                      {h.artifacts?.vtt && <a className="underline text-blue-300" href={h.artifacts.vtt} target="_blank">VTT</a>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {history.length>0 && <div className="mt-3"><Button variant="danger" onClick={()=>setHistory([])}>Borrar historial local</Button></div>}
      </Card>
    </div>
  );

  // -------------------- Layout --------------------
  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-950 to-zinc-900 text-zinc-100">
      <div className="max-w-6xl mx-auto px-4 py-6">
        <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
          <div>
            <div className="text-3xl font-black">Speech2Text X</div>
            <div className="text-xs text-zinc-400">API: {apiBase}</div>
          </div>
          <nav className="flex items-center gap-2">
            {[
              {id:"home", label:"Inicio"},
              {id:"transcribe", label:"Transcribir"},
              {id:"library", label:"Biblioteca"},
              {id:"history", label:"Historial"},
            ].map(it=>(
              <button key={it.id} onClick={()=>setTab(it.id)} className={cx(
                "px-3 py-2 rounded-xl text-sm border",
                tab===it.id ? "bg-blue-600 border-blue-500 text-white" : "bg-zinc-900/40 border-zinc-800 hover:bg-zinc-800 text-zinc-200"
              )}>{it.label}</button>
            ))}
          </nav>
        </header>

        {tab==="home" && <HomeView/>}
        {tab==="transcribe" && <TranscribeView/>}
        {tab==="library" && <LibraryView/>}
        {tab==="history" && <HistoryView/>}

        <footer className="mt-10 text-xs text-zinc-500">
          Tip: Puedes resolver enlaces compartidos con <span className="font-mono">/shares/resolve/&lt;token&gt;</span>.
        </footer>
      </div>
    </div>
  );
}
