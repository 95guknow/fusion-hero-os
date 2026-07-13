import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const envPath = resolve(__dirname, "../.env");

try {
  for (const line of readFileSync(envPath, "utf8").split("\n")) {
    const match = line.match(/^\s*([^#=]+)=(.*)$/);
    if (match && !process.env[match[1].trim()]) {
      process.env[match[1].trim()] = match[2].trim();
    }
  }
} catch {
  // .env optional when vars are already in the shell
}

const url = process.env.SUPABASE_URL || process.env.PUBLIC_SUPABASE_URL;
const key = process.env.SUPABASE_PUBLISHABLE_KEY || process.env.PUBLIC_SUPABASE_PUBLISHABLE_KEY;
const projectRef =
  process.env.SUPABASE_PROJECT_REF ||
  process.env.PUBLIC_SUPABASE_PROJECT_REF ||
  "swmmoxhdzarmoupyssqe";

if (!url || !key) {
  console.log(JSON.stringify({ configured: false, error: "missing env" }));
  process.exit(0);
}

const probe = await fetch(`${url.replace(/\/$/, "")}/auth/v1/settings`, {
  headers: { apikey: key, Authorization: `Bearer ${key}` },
})
  .then((r) => ({ ok: r.ok, status: r.status }))
  .catch((e) => ({ ok: false, error: String(e) }));

console.log(
  JSON.stringify({
    configured: true,
    method: "fetch /auth/v1/settings (kein npm-Paket nötig, nur Node >=18 fetch)",
    node_version: process.version,
    project_ref: projectRef,
    dashboard_url: `https://supabase.com/dashboard/project/${projectRef}`,
    secret_key_configured: Boolean(process.env.SUPABASE_SECRET_KEY),
    jwks_url: process.env.SUPABASE_JWKS_URL || null,
    probe,
  }),
);