import type { ForwardedRef, MutableRefObject, TextareaHTMLAttributes } from "react";
import { forwardRef, useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { cn } from "../../lib/utils";

type BaseTextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>;

type TextareaProps = {
  label?: string;
  helperText?: string;
  errorText?: string;
  autoResize?: boolean;
  isInvalid?: boolean;
} & BaseTextareaProps;

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  {
    id,
    className,
    label,
    helperText,
    errorText,
    autoResize = false,
    isInvalid = Boolean(errorText),
    maxLength,
    onChange,
    defaultValue,
    value,
    ...props
  },
  ref: ForwardedRef<HTMLTextAreaElement>
) {
  const generatedId = useId();
  const textareaId = id ?? generatedId;
  const innerRef = useRef<HTMLTextAreaElement | null>(null);
  const [uncontrolledLength, setUncontrolledLength] = useState(() => {
    if (typeof value === "string") {
      return value.length;
    }
    if (typeof defaultValue === "string") {
      return defaultValue.length;
    }
    return 0;
  });

  const currentLength = useMemo(() => {
    if (typeof value === "string") {
      return value.length;
    }
    return uncontrolledLength;
  }, [value, uncontrolledLength]);

  const resize = useCallback(() => {
    if (!autoResize) {
      return;
    }

    const element = innerRef.current;
    if (!element) {
      return;
    }

    element.style.height = "auto";
    element.style.height = `${element.scrollHeight}px`;
  }, [autoResize]);

  useEffect(() => {
    if (!autoResize) {
      return;
    }
    resize();
  }, [autoResize, resize, value, defaultValue]);

  const handleChange: BaseTextareaProps["onChange"] = (event) => {
    if (typeof value !== "string") {
      setUncontrolledLength(event.target.value.length);
    }

    resize();
    onChange?.(event);
  };

  const helperOrError = errorText ?? helperText;
  const descriptionId = helperOrError ? `${textareaId}-description` : undefined;
  const counterId = typeof maxLength === "number" ? `${textareaId}-counter` : undefined;

  return (
    <div className="flex flex-col gap-2">
      {label ? (
        <label htmlFor={textareaId} className="text-sm font-medium text-white">
          {label}
        </label>
      ) : null}
      <textarea
        id={textareaId}
        ref={(node) => {
          innerRef.current = node;
          if (typeof ref === "function") {
            ref(node);
          } else if (ref) {
            (ref as MutableRefObject<HTMLTextAreaElement | null>).current = node;
          }
        }}
        className={cn(
          "min-h-[120px] w-full rounded-md border border-transparent bg-secondary/20 px-3 py-2 text-sm text-white placeholder:text-secondary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
          autoResize ? "resize-none" : "resize-y",
          isInvalid ? "border-danger focus-visible:ring-danger" : "border-transparent",
          className
        )}
        maxLength={maxLength}
        onChange={handleChange}
        defaultValue={defaultValue}
        value={value}
        aria-invalid={isInvalid || undefined}
        aria-describedby={[descriptionId, counterId].filter(Boolean).join(" ") || undefined}
        {...props}
      />
      {(helperOrError || typeof maxLength === "number") && (
        <div className="flex items-start justify-between text-xs">
          <span
            id={descriptionId}
            className={cn("text-secondary/70", errorText && "text-danger")}
          >
            {helperOrError}
          </span>
          {typeof maxLength === "number" ? (
            <span id={counterId} className="text-secondary/60">{currentLength} / {maxLength}</span>
          ) : null}
        </div>
      )}
    </div>
  );
});
