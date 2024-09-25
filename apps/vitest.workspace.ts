import { defineWorkspace } from "vitest/config";

export default defineWorkspace([
  "./dashboard/vitest.config.ts",
  "./shared/vitest.config.ts",
  "./demo/vitest.config.ts",
]);
