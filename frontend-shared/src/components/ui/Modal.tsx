import { AnimatePresence, motion } from "framer-motion";
import {
  createContext,
  type ComponentPropsWithoutRef,
  type HTMLAttributes,
  type RefObject,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState
} from "react";
import { createPortal } from "react-dom";
import { cn } from "../../lib/utils";

type ModalSize = "sm" | "md" | "lg" | "xl" | "full";
type ModalAlign = "center" | "top";

interface ModalContextValue {
  onClose: () => void;
  labelledBy?: string;
  describedBy?: string;
  setLabelledBy: (id?: string) => void;
  setDescribedBy: (id?: string) => void;
}

const ModalContext = createContext<ModalContextValue | null>(null);

function useModalContext(component: string): ModalContextValue {
  const context = useContext(ModalContext);
  if (!context) {
    throw new Error(`${component} must be used within a Modal`);
  }
  return context;
}

const FOCUSABLE_SELECTORS = [
  "a[href]",
  "area[href]",
  "button:not([disabled])",
  "input:not([disabled]):not([type=hidden])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "iframe",
  "object",
  "embed",
  "[tabindex]:not([tabindex='-1'])",
  "[contenteditable='true']"
].join(",");

const sizeClasses: Record<ModalSize, string> = {
  sm: "max-w-md",
  md: "max-w-lg",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
  full: "w-full h-full"
};

const alignClasses: Record<ModalAlign, string> = {
  center: "items-center",
  top: "items-start pt-16"
};

type MotionDivProps = ComponentPropsWithoutRef<typeof motion.div>;

export interface ModalProps
  extends Omit<MotionDivProps, "children" | "role" | "aria-modal" | "aria-labelledby" | "aria-describedby"> {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  size?: ModalSize;
  align?: ModalAlign;
  trapFocus?: boolean;
  closeOnOverlayClick?: boolean;
  closeOnEsc?: boolean;
  initialFocusRef?: RefObject<HTMLElement>;
  restoreFocus?: boolean;
  portalTarget?: HTMLElement | null;
  backdropClassName?: string;
}

const defaultPortalId = "ninaivalaigal-modal-root";

function getFocusableElements(container: HTMLElement | null): HTMLElement[] {
  if (!container) {
    return [];
  }
  const nodes = Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS));
  return nodes.filter((node) => !node.hasAttribute("disabled") && node.tabIndex !== -1 && node.offsetParent !== null);
}

function createPortalNode(target?: HTMLElement | null): HTMLElement | null {
  if (typeof window === "undefined") {
    return null;
  }
  if (target) {
    return target;
  }
  let root = document.getElementById(defaultPortalId);
  if (!root) {
    root = document.createElement("div");
    root.setAttribute("id", defaultPortalId);
    document.body.appendChild(root);
  }
  return root;
}

function ModalComponent({
  isOpen,
  onClose,
  children,
  size = "md",
  align = "center",
  trapFocus = true,
  closeOnOverlayClick = true,
  closeOnEsc = true,
  initialFocusRef,
  restoreFocus = true,
  portalTarget,
  className,
  backdropClassName,
  ...rest
}: ModalProps) {
  const [labelledBy, setLabelledBy] = useState<string | undefined>(undefined);
  const [describedBy, setDescribedBy] = useState<string | undefined>(undefined);
  const contentRef = useRef<HTMLDivElement | null>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const [portalNode, setPortalNode] = useState<HTMLElement | null>(() => createPortalNode(portalTarget ?? null));

  const setContentRef = useCallback((node: HTMLDivElement | null) => {
    contentRef.current = node;
  }, []);

  useEffect(() => {
    setPortalNode(createPortalNode(portalTarget ?? null));
  }, [portalTarget]);

  useEffect(() => {
    if (!isOpen || typeof window === "undefined") {
      return;
    }
    previousFocusRef.current = document.activeElement as HTMLElement | null;

    const focusTarget = initialFocusRef?.current ?? getFocusableElements(contentRef.current)[0];
    focusTarget?.focus();

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = originalOverflow;
      if (restoreFocus) {
        previousFocusRef.current?.focus?.();
        previousFocusRef.current = null;
      }
    };
  }, [initialFocusRef, isOpen, restoreFocus]);

  useEffect(() => {
    if (!trapFocus || !isOpen) {
      return;
    }

    const node = contentRef.current;
    if (!node) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Tab") {
        const focusable = getFocusableElements(contentRef.current);
        if (focusable.length === 0) {
          event.preventDefault();
          return;
        }
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        const active = document.activeElement as HTMLElement | null;
        if (event.shiftKey) {
          if (active === first || !focusable.includes(active as HTMLElement)) {
            event.preventDefault();
            last.focus();
          }
        } else if (active === last || !focusable.includes(active as HTMLElement)) {
          event.preventDefault();
          first.focus();
        }
      } else if (event.key === "Escape" && closeOnEsc) {
        event.preventDefault();
        onClose();
      }
    };

    node.addEventListener("keydown", handleKeyDown);
    return () => {
      node.removeEventListener("keydown", handleKeyDown);
    };
  }, [closeOnEsc, isOpen, onClose, trapFocus]);

  useEffect(() => {
    if (!isOpen || !closeOnEsc) {
      return;
    }
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [closeOnEsc, isOpen, onClose]);

  const contextValue = useMemo<ModalContextValue>(
    () => ({
      onClose,
      labelledBy,
      describedBy,
      setLabelledBy,
      setDescribedBy
    }),
    [describedBy, labelledBy, onClose]
  );

  if (!portalNode) {
    return null;
  }

  return createPortal(
    <AnimatePresence>
      {isOpen ? (
        <ModalContext.Provider value={contextValue}>
          <motion.div
            className={cn(
              "fixed inset-0 z-[1000] flex justify-center bg-black/40 px-4 sm:px-6",
              alignClasses[align],
              backdropClassName
            )}
            data-testid="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onMouseDown={(event) => {
              if (!closeOnOverlayClick) {
                return;
              }
              if (event.target === event.currentTarget) {
                onClose();
              }
            }}
          >
            <motion.div
              ref={setContentRef}
              role="dialog"
              aria-modal="true"
              aria-labelledby={labelledBy}
              aria-describedby={describedBy}
              className={cn(
                "relative w-full transform rounded-xl bg-white shadow-2xl transition-all dark:bg-slate-900",
                sizeClasses[size],
                className
              )}
              initial={{ opacity: 0, scale: 0.97, y: align === "top" ? -12 : 0 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.97, y: align === "top" ? -12 : 0 }}
              transition={{ duration: 0.2 }}
              {...rest}
            >
              {children}
            </motion.div>
          </motion.div>
        </ModalContext.Provider>
      ) : null}
    </AnimatePresence>,
    portalNode
  );
}

interface ModalSectionProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

function ModalHeader({ children, className, ...rest }: ModalSectionProps) {
  return (
    <div className={cn("flex items-start justify-between gap-3 border-b border-slate-200 px-6 py-5 dark:border-slate-800", className)} {...rest}>
      {children}
    </div>
  );
}

function ModalBody({ children, className, ...rest }: ModalSectionProps) {
  return (
    <div className={cn("px-6 py-4 text-slate-700 dark:text-slate-200", className)} {...rest}>
      {children}
    </div>
  );
}

function ModalFooter({ children, className, ...rest }: ModalSectionProps) {
  return (
    <div className={cn("flex flex-col-reverse gap-3 border-t border-slate-200 px-6 py-4 sm:flex-row sm:justify-end dark:border-slate-800", className)} {...rest}>
      {children}
    </div>
  );
}

interface ModalTitleProps extends HTMLAttributes<HTMLHeadingElement> {
  children: ReactNode;
}

function ModalTitle({ children, className, id, ...rest }: ModalTitleProps) {
  const { setLabelledBy } = useModalContext("Modal.Title");
  const autoId = useId();
  const resolvedId = id ?? autoId;

  useEffect(() => {
    setLabelledBy(resolvedId);
    return () => setLabelledBy(undefined);
  }, [resolvedId, setLabelledBy]);

  return (
    <h2 id={resolvedId} className={cn("text-lg font-semibold text-slate-900 dark:text-white", className)} {...rest}>
      {children}
    </h2>
  );
}

interface ModalDescriptionProps extends HTMLAttributes<HTMLParagraphElement> {
  children: ReactNode;
}

function ModalDescription({ children, className, id, ...rest }: ModalDescriptionProps) {
  const { setDescribedBy } = useModalContext("Modal.Description");
  const autoId = useId();
  const resolvedId = id ?? autoId;

  useEffect(() => {
    setDescribedBy(resolvedId);
    return () => setDescribedBy(undefined);
  }, [resolvedId, setDescribedBy]);

  return (
    <p id={resolvedId} className={cn("mt-1 text-sm text-slate-600 dark:text-slate-300", className)} {...rest}>
      {children}
    </p>
  );
}

interface ModalCloseButtonProps extends HTMLAttributes<HTMLButtonElement> {
  label?: string;
}

function ModalCloseButton({ className, label = "Close dialog", ...rest }: ModalCloseButtonProps) {
  const { onClose } = useModalContext("Modal.CloseButton");

  return (
    <button
      type="button"
      onClick={onClose}
      aria-label={label}
      className={cn(
        "inline-flex h-9 w-9 items-center justify-center rounded-md border border-transparent text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100 dark:focus-visible:ring-slate-600",
        className
      )}
      {...rest}
    >
      <span aria-hidden="true">×</span>
    </button>
  );
}

interface ModalActions extends React.FC<ModalProps> {
  Header: typeof ModalHeader;
  Body: typeof ModalBody;
  Footer: typeof ModalFooter;
  Title: typeof ModalTitle;
  Description: typeof ModalDescription;
  CloseButton: typeof ModalCloseButton;
}

export const Modal = Object.assign(ModalComponent, {
  Header: ModalHeader,
  Body: ModalBody,
  Footer: ModalFooter,
  Title: ModalTitle,
  Description: ModalDescription,
  CloseButton: ModalCloseButton
}) as ModalActions;
