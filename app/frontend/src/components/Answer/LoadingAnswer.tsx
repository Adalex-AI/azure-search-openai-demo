import React from "react";
import styles from "./Answer.module.css";

/**
 * LoadingAnswer Component
 *
 * Displays a professional loading state with animated dots while waiting for AI response.
 * Similar to ChatGPT and Gemini loading animations.
 */
export const LoadingAnswer: React.FC = () => {
    return (
        <div className={styles.loadingAnswer}>
            <div className={styles.loadingDot} />
            <div className={styles.loadingDot} />
            <div className={styles.loadingDot} />
        </div>
    );
};

export default LoadingAnswer;
