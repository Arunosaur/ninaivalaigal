import { AnimatePresence, motion } from "framer-motion";
import {
  Fragment,
  type KeyboardEvent,
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState
} from "react";
import { cn } from "../../lib/utils";

type SelectVariant = "custom" | "native";

export interface SelectOption<TValue extends string | number> {
  value: TValue;
  label: string;
  description?: string;
  disabled?: boolean;
}

interface BaseSelectProps<TValue extends string | number> {
  id?: string;
  label?: string;
  helperText?: string;
  placeholder?: string;
  error?: string | boolean;
  disabled?: boolean;
  className?: string;
  variant?: SelectVariant;
  searchable?: boolean;
  multi?: boolean;
  maxVisibleTags?: number;
  searchPlaceholder?: string;
  onSearchChange?: (search: string) => void;
}

interface SingleSelectProps<TValue extends string | number> extends BaseSelectProps<TValue> {
  value: TValue | null;
  defaultValue?: never;
  onChange: (value: TValue | null) => void;
  options: Array<SelectOption<TValue>>;
}

interface MultiSelectProps<TValue extends string | number> extends BaseSelectProps<TValue> {
  value: Array<TValue>;
  defaultValue?: never;
  onChange: (value: Array<TValue>) => void;
  options: Array<SelectOption<TValue>>;
  multi: true;
}

export type SelectProps<TValue extends string | number> = SingleSelectProps<TValue> | MultiSelectProps<TValue>;

const listboxVariants = {
  initial: { opacity: 0, y: -4 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -4 }
};

const baseFieldClasses =
  "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm transition focus-within:ring-2 focus-within:ring-primary focus-within:ring-offset-0 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100";

const controlClasses =
  "flex min-h-[40px] items-center justify-between gap-2 rounded-md px-3 py-2 text-left text-sm outline-none";

export function Select<TValue extends string | number>({
  id,
  label,
  helperText,
  placeholder = "Select an option",
  error,
  disabled = false,
  className,
  variant = "custom",
  searchable = true,
  multi = false,
  maxVisibleTags = 3,
  searchPlaceholder = "Search",
  onSearchChange,
  value,
  onChange,
  options
}: SelectProps<TValue>) {
  const selectId = useId();
  const internalId = id ?? `select-${selectId}`;
  const listboxId = `${internalId}-listbox`;
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const popoverRef = useRef<HTMLDivElement | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const isOpenRef = useRef(isOpen);
  const [search, setSearch] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState<number>(-1);

  const hasErrorMessage = typeof error === "string" && error.length > 0;

  const filteredOptions = useMemo(() => {
    if (!searchable || search.trim().length === 0) {
      return options;
    }
    const needle = search.toLowerCase();
    return options.filter((option) => option.label.toLowerCase().includes(needle));
  }, [options, search, searchable]);

  const selectedOptions = useMemo(() => {
    if (multi) {
      const values = new Set(value as Array<TValue>);
      return options.filter((option) => values.has(option.value));
    }
    return options.filter((option) => option.value === value);
  }, [multi, options, value]);

  const handleOpen = useCallback(
    (open: boolean) => {
      if (disabled) {
        return;
      }
      isOpenRef.current = open;
      setIsOpen(open);
      if (!open) {
        setHighlightedIndex(-1);
        setSearch("");
        onSearchChange?.("");
      }
    },
    [disabled, onSearchChange]
  );

  useEffect(() => {
    isOpenRef.current = isOpen;
  }, [isOpen]);

  const commitChanges = useCallback(
    (option: SelectOption<TValue>) => {
      if (option.disabled) {
        return;
      }
      if (multi) {
        const current = new Set((value as Array<TValue>) ?? []);
        if (current.has(option.value)) {
          current.delete(option.value);
        } else {
          current.add(option.value);
        }
        (onChange as MultiSelectProps<TValue>["onChange"])(Array.from(current));
      } else {
        const nextValue = option.value === value ? null : option.value;
        (onChange as SingleSelectProps<TValue>["onChange"])(nextValue as TValue | null);
        handleOpen(false);
        triggerRef.current?.focus();
      }
    },
    [handleOpen, multi, onChange, value]
  );

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const handleClickOutside = (event: MouseEvent) => {
      if (!popoverRef.current || popoverRef.current.contains(event.target as Node)) {
        return;
      }
      if (triggerRef.current && triggerRef.current.contains(event.target as Node)) {
        return;
      }
      handleOpen(false);
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [handleOpen, isOpen]);

  useEffect(() => {
    if (isOpen && searchable && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen, searchable]);

  const renderSelectedLabel = () => {
    if (multi) {
      if (selectedOptions.length === 0) {
        return <span className="text-slate-400">{placeholder}</span>;
      }
      const visible = selectedOptions.slice(0, maxVisibleTags);
      const remaining = selectedOptions.length - visible.length;
      return (
        <div className="flex flex-wrap items-center gap-1">
          {visible.map((option) => (
            <span
              key={option.value}
              className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary"
            >
              {option.label}
              <span
                role="button"
                tabIndex={-1}
                aria-label={`Remove ${option.label}`}
                onMouseDown={(event) => event.preventDefault()}
                onClick={(event) => {
                  event.stopPropagation();
                  commitChanges(option);
                }}
                className="ml-1 inline-flex h-4 w-4 items-center justify-center rounded-full text-primary hover:bg-primary/10"
              >
                ×
              </span>
            </span>
          ))}
          {remaining > 0 ? <span className="text-xs text-slate-500">+{remaining} more</span> : null}
        </div>
      );
    }

    const option = selectedOptions[0];
    if (!option) {
      return <span className="text-slate-400">{placeholder}</span>;
    }
    return <span>{option.label}</span>;
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (disabled) {
      return;
    }
    const open = isOpenRef.current;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (!open) {
        handleOpen(true);
        setHighlightedIndex(0);
        return;
      }
      setHighlightedIndex((prev) => {
        if (filteredOptions.length === 0) {
          return -1;
        }
        const next = prev + (event.key === "ArrowDown" ? 1 : -1);
        if (next < 0) {
          return filteredOptions.length - 1;
        }
        if (next >= filteredOptions.length) {
          return 0;
        }
        return next;
      });
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (!open) {
        handleOpen(true);
        setHighlightedIndex(0);
        return;
      }
      const option = filteredOptions[highlightedIndex];
      if (option) {
        commitChanges(option);
      }
    } else if (event.key === "Escape") {
      event.preventDefault();
      handleOpen(false);
    } else if (event.key === "Home") {
      event.preventDefault();
      setHighlightedIndex(filteredOptions.length > 0 ? 0 : -1);
    } else if (event.key === "End") {
      event.preventDefault();
      setHighlightedIndex(filteredOptions.length - 1);
    }
  };

  useEffect(() => {
    if (highlightedIndex >= filteredOptions.length) {
      setHighlightedIndex(filteredOptions.length - 1);
    }
  }, [filteredOptions, highlightedIndex]);

  if (variant === "native") {
    const stringifiedValue = multi
      ? ((value as Array<TValue>) ?? []).map((item) => String(item))
      : value === null || value === undefined
      ? ""
      : String(value as TValue);

    const resolveValue = (raw: string): TValue => {
      const match = options.find((option) => String(option.value) === raw);
      return (match ? match.value : (raw as unknown as TValue)) as TValue;
    };

    return (
      <div className={cn("space-y-1", className)}>
        {label ? (
          <label htmlFor={internalId} className="block text-sm font-medium text-slate-700 dark:text-slate-200">
            {label}
          </label>
        ) : null}
        <select
          id={internalId}
          role="combobox"
          disabled={disabled}
          className={cn(
            baseFieldClasses,
            "text-sm focus:outline-none focus:ring-2 focus:ring-primary",
            disabled ? "cursor-not-allowed opacity-60" : null,
            hasErrorMessage || error ? "border-danger focus:ring-danger" : null
          )}
          value={stringifiedValue}
          multiple={multi}
          onChange={(event) => {
            if (multi) {
              const selectedValues = Array.from(event.target.selectedOptions).map((option) => resolveValue(option.value));
              (onChange as MultiSelectProps<TValue>["onChange"])(selectedValues);
            } else {
              const rawValue = event.target.value;
              const selected = rawValue === "" ? null : resolveValue(rawValue);
              (onChange as SingleSelectProps<TValue>["onChange"])(selected);
            }
          }}
        >
          {!multi ? (
            <option value="" disabled>
              {placeholder}
            </option>
          ) : null}
          {options.map((option) => (
            <option key={option.value} value={option.value} disabled={option.disabled}>
              {option.label}
            </option>
          ))}
        </select>
        {helperText && !error ? <p className="text-xs text-slate-500 dark:text-slate-400">{helperText}</p> : null}
        {hasErrorMessage ? <p className="text-xs text-danger">{error}</p> : null}
      </div>
    );
  }

  return (
    <div className={cn("space-y-1", className)}>
      {label ? (
        <label htmlFor={`${internalId}-trigger`} className="block text-sm font-medium text-slate-700 dark:text-slate-200">
          {label}
        </label>
      ) : null}
      <div
        className={cn(
          baseFieldClasses,
          "relative",
          disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer",
          hasErrorMessage || error ? "border-danger focus-within:ring-danger" : null
        )}
      >
        <button
          type="button"
          id={`${internalId}-trigger`}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          aria-controls={listboxId}
          ref={triggerRef}
          className={cn(controlClasses, disabled ? "pointer-events-none" : null)}
          disabled={disabled}
          onClick={() => handleOpen(!isOpen)}
          onKeyDown={handleKeyDown}
        >
          <span className="flex-1 truncate">{renderSelectedLabel()}</span>
          <span className="ml-2 text-slate-400" aria-hidden="true">
            ▾
          </span>
        </button>

        <AnimatePresence>
          {isOpen ? (
            <motion.div
              ref={popoverRef}
              className="absolute z-20 mt-1 w-full overflow-hidden rounded-md border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-900"
              variants={listboxVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              role="presentation"
            >
              {searchable ? (
                <div className="border-b border-slate-200 px-3 py-2 dark:border-slate-800">
                  <input
                    ref={searchInputRef}
                    type="text"
                    value={search}
                    onChange={(event) => {
                      setSearch(event.target.value);
                      onSearchChange?.(event.target.value);
                    }}
                    placeholder={searchPlaceholder}
                    className="w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                  />
                </div>
              ) : null}
              <ul
                id={listboxId}
                role="listbox"
                aria-multiselectable={multi}
                className="max-h-60 overflow-auto py-1"
              >
                {filteredOptions.length === 0 ? (
                  <li className="px-3 py-2 text-sm text-slate-500">No results found</li>
                ) : (
                  filteredOptions.map((option, index) => {
                    const active = highlightedIndex === index;
                    const selected = multi
                      ? (value as Array<TValue>).includes(option.value)
                      : option.value === value;

                    return (
                      <Fragment key={option.value}>
                        <li
                          role="option"
                          aria-selected={selected}
                          aria-disabled={option.disabled}
                          className={cn(
                            "flex cursor-pointer select-none flex-col gap-0.5 px-3 py-2 text-sm",
                            selected ? "bg-primary/10 text-primary" : "text-slate-700 dark:text-slate-200",
                            active ? "bg-primary/10" : null,
                            option.disabled ? "cursor-not-allowed opacity-50" : null
                          )}
                          onMouseEnter={() => setHighlightedIndex(index)}
                          onMouseDown={(event) => event.preventDefault()}
                          onClick={() => commitChanges(option)}
                        >
                          <span className="font-medium">{option.label}</span>
                          {option.description ? (
                            <span className="text-xs text-slate-500 dark:text-slate-400">{option.description}</span>
                          ) : null}
                        </li>
                      </Fragment>
                    );
                  })
                )}
              </ul>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>
      {helperText && !error ? <p className="text-xs text-slate-500 dark:text-slate-400">{helperText}</p> : null}
      {hasErrorMessage ? <p className="text-xs text-danger">{error}</p> : null}
    </div>
  );
}
