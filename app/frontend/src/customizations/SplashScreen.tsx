import React, { useState, useEffect, useCallback } from "react";
import styles from "./SplashScreen.module.css";

// CUSTOM: Default logo using the same SVG as the main app
// Can be replaced with a custom logo if needed
const DefaultLogo = () => (
    <svg className={styles.logoIcon} viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <path
            d="M7.4 12.8a1.04 1.04 0 0 0 1.59-.51l.45-1.37a2.34 2.34 0 0 1 1.47-1.48l1.4-.45A1.04 1.04 0 0 0 12.25 7l-1.37-.45A2.34 2.34 0 0 1 9.4 5.08L8.95 3.7a1.03 1.03 0 0 0-.82-.68 1.04 1.04 0 0 0-1.15.7l-.46 1.4a2.34 2.34 0 0 1-1.44 1.45L3.7 7a1.04 1.04 0 0 0 .02 1.97l1.37.45a2.33 2.33 0 0 1 1.48 1.48l.46 1.4c.07.2.2.37.38.5Zm6.14 4.05a.8.8 0 0 0 1.22-.4l.25-.76a1.09 1.09 0 0 1 .68-.68l.77-.25a.8.8 0 0 0-.02-1.52l-.77-.25a1.08 1.08 0 0 1-.68-.68l-.25-.77a.8.8 0 0 0-1.52.01l-.24.76a1.1 1.1 0 0 1-.67.68l-.77.25a.8.8 0 0 0 0 1.52l.77.25a1.09 1.09 0 0 1 .68.68l.25.77c.06.16.16.3.3.4Z"
            fill="currentColor"
        />
    </svg>
);

interface SplashScreenProps {
    /** Title to display on splash screen */
    title?: string;
    /** Subtitle or tagline */
    subtitle?: string;
    /** Duration in ms to show centered content before morphing (default: 1800ms) */
    duration?: number;
    /** Callback when splash screen finishes */
    onComplete?: () => void;
    /** Custom logo element (optional) */
    logo?: React.ReactNode;
    /** Skip splash if user has visited before (uses sessionStorage) */
    skipOnRevisit?: boolean;
    /** Session storage key for tracking visits */
    storageKey?: string;
}

/**
 * SplashScreen Component
 *
 * A professional animated splash screen that displays on first load.
 * Features:
 * - Smooth fade-in animation for centered content
 * - Content morphs/shrinks and moves to top-left header position
 * - Respects prefers-reduced-motion
 * - Click/keyboard to skip
 * - Session-based skip on revisit
 */
export const SplashScreen: React.FC<SplashScreenProps> = ({
    title = "Civil Procedure Copilot",
    subtitle = "Your AI assistant for Civil Procedure Rules, Practice Directions, and Court Guides",
    duration = 1800,
    onComplete,
    logo,
    skipOnRevisit = true,
    storageKey = "cpr-splash-shown"
}) => {
    const [phase, setPhase] = useState<"appearing" | "visible" | "morphing" | "done">("appearing");

    // Check if user prefers reduced motion
    const prefersReducedMotion = typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

    // Check if splash was already shown this session
    const wasShownThisSession = skipOnRevisit && typeof sessionStorage !== "undefined" && sessionStorage.getItem(storageKey) === "true";

    const handleDismiss = useCallback(() => {
        if (phase === "morphing" || phase === "done") return; // Already transitioning

        // Store that splash was shown
        if (skipOnRevisit && typeof sessionStorage !== "undefined") {
            sessionStorage.setItem(storageKey, "true");
        }

        // Start morphing animation
        setPhase("morphing");

        // Wait for morph animation to complete, then hide
        const morphDuration = prefersReducedMotion ? 0 : 700;
        setTimeout(() => {
            setPhase("done");
            onComplete?.();
        }, morphDuration);
    }, [phase, onComplete, prefersReducedMotion, skipOnRevisit, storageKey]);

    // Handle keyboard events (Escape or Enter to skip)
    const handleKeyDown = useCallback(
        (e: KeyboardEvent) => {
            if (e.key === "Escape" || e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleDismiss();
            }
        },
        [handleDismiss]
    );

    // Handle click to skip
    const handleClick = useCallback(() => {
        handleDismiss();
    }, [handleDismiss]);

    // Set up animation phases
    useEffect(() => {
        // Skip immediately if already shown this session
        if (wasShownThisSession) {
            setPhase("done");
            onComplete?.();
            return;
        }

        // Skip immediately if user prefers reduced motion
        if (prefersReducedMotion) {
            if (skipOnRevisit && typeof sessionStorage !== "undefined") {
                sessionStorage.setItem(storageKey, "true");
            }
            setPhase("done");
            onComplete?.();
            return;
        }

        // Phase 1: Appearing (fade in) - takes ~800ms
        const appearTimer = setTimeout(() => {
            setPhase("visible");
        }, 800);

        // Phase 2: Visible (hold) - then start morphing
        const morphTimer = setTimeout(() => {
            handleDismiss();
        }, duration);

        // Set up keyboard listener
        document.addEventListener("keydown", handleKeyDown);

        return () => {
            clearTimeout(appearTimer);
            clearTimeout(morphTimer);
            document.removeEventListener("keydown", handleKeyDown);
        };
    }, [duration, handleDismiss, handleKeyDown, onComplete, prefersReducedMotion, skipOnRevisit, storageKey, wasShownThisSession]);

    // Don't render if done
    if (phase === "done") {
        return null;
    }

    const isMorphing = phase === "morphing";

    return (
        <div
            className={`${styles.splashOverlay} ${isMorphing ? styles.morphing : styles.fadeIn}`}
            onClick={handleClick}
            role="dialog"
            aria-modal="true"
            aria-label={`${title} - ${subtitle}`}
            tabIndex={0}
        >
            <div className={`${styles.splashContent} ${isMorphing ? styles.contentMorphing : ""}`}>
                {/* Logo with animation */}
                <div className={`${styles.logoContainer} ${isMorphing ? styles.logoMorphing : ""}`}>{logo || <DefaultLogo />}</div>

                {/* Title with staggered animation */}
                <h1 className={`${styles.title} ${isMorphing ? styles.titleMorphing : ""}`}>{title}</h1>

                {/* Subtitle with delayed animation - fades out during morph */}
                <p className={`${styles.subtitle} ${isMorphing ? styles.subtitleMorphing : ""}`}>{subtitle}</p>
            </div>
        </div>
    );
};

export default SplashScreen;
