import React, { useEffect, useState } from "react";
import { Dropdown, IDropdownOption, IDropdownStyles } from "@fluentui/react";

interface CategoryDropdownProps {
    selectedCategory: string;
    onChange: (category: string) => void;
    multiSelect?: boolean;
    compact?: boolean;
    disabled?: boolean;
    placeholder?: string;
}

interface ApiCategory {
    key: string;
    text: string;
    count?: number | null;
}

export const CategoryDropdown: React.FC<CategoryDropdownProps> = ({
    selectedCategory,
    onChange,
    multiSelect = false,
    compact = false,
    disabled = false,
    placeholder = "Select category"
}) => {
    const [categories, setCategories] = useState<ApiCategory[]>([{ key: "", text: "All Categories" }]);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let mounted = true;
        const run = async () => {
            try {
                setLoading(true);
                setError(null);
                const res = await fetch("/api/categories");
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const json = await res.json();
                const items: ApiCategory[] = (json?.categories as ApiCategory[]) || [];
                // Remove any API-provided "All" (empty key) and prepend a single local "All Categories"
                const filtered = items.filter(c => (c.key ?? "") !== "");
                if (mounted) setCategories([{ key: "", text: "All Categories" }, ...filtered]);
            } catch (e) {
                if (mounted) setError("Failed to load categories");
            } finally {
                if (mounted) setLoading(false);
            }
        };
        run();
        return () => {
            mounted = false;
        };
    }, []);

    const dropdownStyles: Partial<IDropdownStyles> = {
        dropdown: { width: compact ? 200 : 300, marginRight: compact ? "8px" : undefined }
    };

    const handleChange = (_: any, option?: IDropdownOption) => {
        if (!option) return;
        // Special-case "All" to clear selection
        if (option.key === "") {
            onChange("");
            return;
        }
        if (multiSelect) {
            const current = selectedCategory
                .split(",")
                .map(s => s.trim())
                .filter(Boolean);
            const next = option.selected ? Array.from(new Set([...current, option.key as string])) : current.filter(c => c !== option.key);
            onChange(next.join(","));
        } else {
            onChange(option.key as string);
        }
    };

    const selectedKeys = multiSelect
        ? selectedCategory.trim() === ""
            ? [] // show no selection so backend court detection/CPR fallback applies
            : selectedCategory.split(",").map(s => s.trim()).filter(Boolean)
        : selectedCategory !== undefined
          ? [selectedCategory === "" ? "" : selectedCategory]
          : [""];

    return (
        <Dropdown
            placeholder={loading ? "Loading categories..." : placeholder}
            options={categories.map(c => ({ key: c.key, text: c.count ? `${c.text} (${c.count})` : c.text }))}
            selectedKeys={selectedKeys}
            onChange={handleChange}
            multiSelect={multiSelect}
            disabled={disabled || loading}
            styles={dropdownStyles}
            errorMessage={error ?? undefined}
            onRenderOption={(option?: IDropdownOption) => (
                <div title={option?.text as string} style={{ whiteSpace: "normal", lineHeight: 1.2 }}>
                    {option?.text}
                </div>
            )}
            onRenderTitle={(items?: IDropdownOption[]) => {
                const full = (items || []).map(i => i.text).join(", ");
                return (
                    <div title={full} style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {full || "All Categories"}
                    </div>
                );
            }}
        />
    );
};
