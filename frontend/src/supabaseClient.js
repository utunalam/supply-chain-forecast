import { createClient } from "@supabase/supabase-js";

// Both values are PUBLIC and safe in the browser.
// Never put the service_role key or database password in a VITE_ variable.
const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabaseConfigured = Boolean(url && anonKey);

export const supabase = supabaseConfigured ? createClient(url, anonKey) : null;
