// apps/web-research/src/components/ResearchConfig.tsx
import type { Config } from "../App";
import type { ServedPolicy } from "../api/client";

interface Props {
  config: Config;
  onChange: (c: Config) => void;
}

export default function ResearchConfig({ config, onChange }: Props) {
  function set<K extends keyof Config>(key: K, val: Config[K]) {
    onChange({ ...config, [key]: val });
  }

  return (
    <section className="card">
      <h2>⚙️ Research Config</h2>

      {/* Serving Policy */}
      <label>Serving Policy</label>
      <div className="radio-group">
        {(["rule", "ltr"] as ServedPolicy[]).map((p) => (
          <label key={p} className="radio-label">
            <input
              type="radio"
              name="policy"
              value={p}
              checked={config.served_policy === p}
              onChange={() => set("served_policy", p)}
            />
            {p.toUpperCase()}
          </label>
        ))}
      </div>

      {/* Model Version (LTR) */}
      <label>Active Model Version</label>
      <input
        type="text"
        placeholder="latest (자동)"
        value={config.active_model_version}
        onChange={(e) => set("active_model_version", e.target.value)}
      />

      {/* Provider Models */}
      <label>OpenAI Model</label>
      <input
        type="text"
        value={config.openai_model}
        onChange={(e) => set("openai_model", e.target.value)}
      />

      <label>Gemini Model</label>
      <input
        type="text"
        value={config.gemini_model}
        onChange={(e) => set("gemini_model", e.target.value)}
      />

      {/* Generation Params */}
      <label>Temperature: {config.temperature}</label>
      <input
        type="range"
        min={0} max={1} step={0.05}
        value={config.temperature}
        onChange={(e) => set("temperature", parseFloat(e.target.value))}
      />

      <label>Max Tokens: {config.max_tokens}</label>
      <input
        type="range"
        min={64} max={1024} step={64}
        value={config.max_tokens}
        onChange={(e) => set("max_tokens", parseInt(e.target.value))}
      />
    </section>
  );
}
