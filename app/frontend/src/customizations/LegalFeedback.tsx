import { useState } from "react";
import { Stack, IconButton, Dialog, DialogFooter, PrimaryButton, DefaultButton, Checkbox, TextField } from "@fluentui/react";

interface Props {
    messageId: string;
}

export const LegalFeedback = ({ messageId }: Props) => {
    const [status, setStatus] = useState<"none" | "helpful" | "unhelpful">("none");
    const [isDialogVisible, setIsDialogVisible] = useState(false);
    const [issues, setIssues] = useState<string[]>([]);
    const [comment, setComment] = useState("");

    const handleVote = (vote: "helpful" | "unhelpful") => {
        setStatus(vote);
        if (vote === "unhelpful") setIsDialogVisible(true);
        else submitFeedback("helpful", [], "");
    };

    const submitFeedback = async (rating: string, selectedIssues: string[], text: string) => {
        try {
            await fetch("/api/feedback", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message_id: messageId,
                    rating,
                    issues: selectedIssues,
                    comment: text
                })
            });
        } catch (e) {
            console.error("Failed to send feedback", e);
        }
        setIsDialogVisible(false);
    };

    const toggleIssue = (issue: string, checked?: boolean) => {
        if (checked) setIssues([...issues, issue]);
        else setIssues(issues.filter(i => i !== issue));
    };

    return (
        <Stack horizontal tokens={{ childrenGap: 8 }} verticalAlign="center">
            <IconButton
                iconProps={{ iconName: status === "helpful" ? "LikeSolid" : "Like" }}
                title="Accurate & Helpful"
                onClick={() => handleVote("helpful")}
                style={{ color: status === "helpful" ? "green" : "inherit" }}
            />
            <IconButton
                iconProps={{ iconName: status === "unhelpful" ? "DislikeSolid" : "Dislike" }}
                title="Report Issue"
                onClick={() => handleVote("unhelpful")}
                style={{ color: status === "unhelpful" ? "red" : "inherit" }}
            />

            <Dialog hidden={!isDialogVisible} onDismiss={() => setIsDialogVisible(false)} dialogContentProps={{ title: "Feedback" }} minWidth={400}>
                <Stack tokens={{ childrenGap: 10 }}>
                    <Checkbox label="Incorrect Citation / Reference" onChange={(_, c) => toggleIssue("wrong_citation", c)} />
                    <Checkbox label="Hallucinated / Fake Citation" onChange={(_, c) => toggleIssue("hallucination", c)} />
                    <Checkbox label="Outdated Law" onChange={(_, c) => toggleIssue("outdated", c)} />
                    <Checkbox label="Missing Key Information" onChange={(_, c) => toggleIssue("missing_info", c)} />
                    <TextField label="Correction / Notes" multiline rows={3} onChange={(_, v) => setComment(v || "")} />
                </Stack>
                <DialogFooter>
                    <PrimaryButton text="Submit Report" onClick={() => submitFeedback("unhelpful", issues, comment)} />
                    <DefaultButton text="Cancel" onClick={() => setIsDialogVisible(false)} />
                </DialogFooter>
            </Dialog>
        </Stack>
    );
};
