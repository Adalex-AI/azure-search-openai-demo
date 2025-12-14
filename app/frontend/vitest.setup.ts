import { afterEach } from "vitest";

// Reset DOM state between tests to avoid leakage from components that touch document-level listeners.
afterEach(() => {
    document.body.innerHTML = "";
});
