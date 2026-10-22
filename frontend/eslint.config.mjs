import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
  {
    rules: {
      // MVP: all data is client-fetched from the FastAPI backend in effects.
      // Revisit when migrating to server components / suspense data fetching.
      "react-hooks/set-state-in-effect": "off",
    },
  },
]);

export default eslintConfig;
