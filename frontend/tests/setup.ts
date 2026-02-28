// TDD: Test setup for frontend tests
// Written from specs 01, 13

import "@testing-library/jest-dom";
import { cleanup } from "@testing-library/react";
import { afterEach, afterAll, beforeAll, vi } from "vitest";
import { server } from "./mocks/server";

// Enable @testing-library/dom to detect Vitest fake timers.
// testing-library checks for `jest.advanceTimersByTime` to enable
// its fake-timer-aware waitFor loop. Without this, waitFor hangs
// when vi.useFakeTimers() is active.
// @ts-expect-error -- jest compatibility shim for testing-library
globalThis.jest = vi;

// Start MSW server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));

// Reset handlers after each test
afterEach(() => {
  cleanup();
  server.resetHandlers();
});

// Close server after all tests
afterAll(() => server.close());
