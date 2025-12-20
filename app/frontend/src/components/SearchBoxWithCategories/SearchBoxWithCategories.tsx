import React, { useState } from "react";
import { Stack, TextField, IconButton } from "@fluentui/react";
import { Send24Regular } from "@fluentui/react-icons";
import { CategoryDropdown } from "../CategoryDropdown/CategoryDropdown";

interface SearchBoxWithCategoriesProps {
    onSearch: (query: string, category?: string) => void;
    disabled?: boolean;
    placeholder?: string;
    clearOnSend?: boolean;
}

export const SearchBoxWithCategories: React.FC<SearchBoxWithCategoriesProps> = ({
    onSearch,
    disabled = false,
    placeholder = "Type a new question...",
    clearOnSend = false
}) => {
    const [query, setQuery] = useState("");
    const [selectedCategory, setSelectedCategory] = useState("");

    const handleSearch = () => {
        if (query.trim()) {
            onSearch(query, selectedCategory || undefined);
            if (clearOnSend) setQuery("");
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSearch();
        }
    };

    return (
        <Stack horizontal tokens={{ childrenGap: 8 }} verticalAlign="center">
            <CategoryDropdown selectedCategory={selectedCategory} onChange={setSelectedCategory} compact={true} disabled={disabled} />
            <TextField
                value={query}
                onChange={(_, newValue) => setQuery(newValue || "")}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                disabled={disabled}
                styles={{ root: { flexGrow: 1 } }}
            />
            <IconButton iconProps={{ iconName: "Send" }} onClick={handleSearch} disabled={disabled || !query.trim()} title="Send" />
        </Stack>
    );
};
