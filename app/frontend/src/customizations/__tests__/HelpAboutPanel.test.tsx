import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { HelpAboutPanel } from "../HelpAboutPanel";

describe("HelpAboutPanel", () => {
    it("opens the panel when clicking the help button", async () => {
        render(<HelpAboutPanel />);

        const button = screen.getByLabelText("Help and About");
        fireEvent.click(button);

        expect(await screen.findByText("Civil Procedure Copilot")).toBeInTheDocument();
        expect(screen.getByText(/Available Documents/i)).toBeInTheDocument();
    });
});
