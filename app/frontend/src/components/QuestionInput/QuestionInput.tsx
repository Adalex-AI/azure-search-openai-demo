import { useState, useEffect, useContext } from "react";
import { Stack, TextField } from "@fluentui/react";
import { Button, Tooltip } from "@fluentui/react-components";
import { Send28Filled } from "@fluentui/react-icons";
import { useTranslation } from "react-i18next";

import styles from "./QuestionInput.module.css";
import { SpeechInput } from "./SpeechInput";
import { LoginContext } from "../../loginContext";
import { requireLogin } from "../../authConfig";

interface Props {
    onSend: (question: string) => void;
    disabled: boolean;
    initQuestion?: string;
    placeholder?: string;
    clearOnSend?: boolean;
    showSpeechInput?: boolean;
    leftOfSend?: React.ReactNode;
}

export const QuestionInput = ({ onSend, disabled, placeholder, clearOnSend, initQuestion, showSpeechInput, leftOfSend }: Props) => {
    const [question, setQuestion] = useState<string>("");
    const { loggedIn } = useContext(LoginContext);
    const { t } = useTranslation();
    const [isComposing, setIsComposing] = useState(false);

    useEffect(() => {
        initQuestion && setQuestion(initQuestion);
    }, [initQuestion]);

    const sendQuestion = () => {
        if (disabled || !question.trim()) {
            return; // Don't send if disabled or no question
        }

        onSend(question);

        // Only clear if clearOnSend is true - let parent handle clearing on success
        // This prevents clearing the question when validation fails
        if (clearOnSend) {
            setQuestion("");
        }
    };

    const onEnterPress = (ev: React.KeyboardEvent<Element>) => {
        if (isComposing) return;

        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            sendQuestion();
        }
    };

    const handleCompositionStart = () => {
        setIsComposing(true);
    };
    const handleCompositionEnd = () => {
        setIsComposing(false);
    };

    const onQuestionChange = (_ev: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        if (!newValue) {
            setQuestion("");
        } else if (newValue.length <= 1000) {
            setQuestion(newValue);
        }
    };

    const disableRequiredAccessControl = requireLogin && !loggedIn;
    const sendQuestionDisabled = disabled || !question.trim() || disableRequiredAccessControl;

    if (disableRequiredAccessControl) {
        placeholder = "Please login to continue...";
    } else if (disabled && placeholder?.includes("category")) {
        // Keep the category-related placeholder if that's why it's disabled
        // placeholder already set by parent component
    }

    return (
        <Stack horizontal className={styles.questionInputContainer} tokens={{ childrenGap: 8 }}>
            <TextField
                className={styles.questionInputTextArea}
                disabled={disableRequiredAccessControl}
                placeholder={placeholder}
                multiline
                resizable={false}
                borderless
                value={question}
                onChange={onQuestionChange}
                onKeyDown={onEnterPress}
                onCompositionStart={handleCompositionStart}
                onCompositionEnd={handleCompositionEnd}
                styles={{
                    root: { flex: 1, minWidth: 0 },
                    fieldGroup: { minHeight: 44 },
                    field: {
                        minHeight: 44,
                        maxHeight: 120,
                        overflowY: "auto",
                        overflowX: "hidden"
                    }
                }}
            />
            <div className={styles.questionInputButtonsContainer}>
                {leftOfSend && <div style={{ marginRight: 8 }}>{leftOfSend}</div>}
                <Tooltip content={t("tooltips.submitQuestion")} relationship="label">
                    <Button 
                        size="large" 
                        icon={<Send28Filled primaryFill="white" />} 
                        disabled={sendQuestionDisabled} 
                        onClick={sendQuestion}
                        style={{
                            backgroundColor: "rgba(115, 118, 225, 1)",
                            color: "white",
                            border: "none",
                            borderRadius: "8px",
                            padding: "8px 12px",
                            transition: "all 0.2s ease",
                            cursor: sendQuestionDisabled ? "not-allowed" : "pointer",
                            opacity: sendQuestionDisabled ? 0.6 : 1,
                            boxShadow: sendQuestionDisabled ? "none" : "0 2px 8px rgba(115, 118, 225, 0.3)"
                        }}
                        onMouseEnter={(e) => {
                            if (!sendQuestionDisabled) {
                                e.currentTarget.style.backgroundColor = "rgba(95, 98, 205, 1)";
                                e.currentTarget.style.boxShadow = "0 4px 12px rgba(115, 118, 225, 0.4)";
                                e.currentTarget.style.transform = "translateY(-2px)";
                            }
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = "rgba(115, 118, 225, 1)";
                            e.currentTarget.style.boxShadow = "0 2px 8px rgba(115, 118, 225, 0.3)";
                            e.currentTarget.style.transform = "translateY(0)";
                        }}
                    />
                </Tooltip>
            </div>
            {showSpeechInput && <SpeechInput updateQuestion={setQuestion} />}
        </Stack>
    );
};
