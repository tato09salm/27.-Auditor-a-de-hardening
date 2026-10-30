import { CheckCircle2, Info, X, XCircle } from "lucide-react";
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import clsx from "clsx";

type ToastTone = "success" | "error" | "info";

interface ToastItem {
  id: string;
  tone: ToastTone;
  title: string;
  message?: string;
}

interface ToastContextValue {
  notify: (toast: { tone?: ToastTone; title: string; message?: string }) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setItems((current) => current.filter((item) => item.id !== id));
  }, []);

  const notify = useCallback(
    ({ tone = "info", title, message }: { tone?: ToastTone; title: string; message?: string }) => {
      const id = crypto.randomUUID();
      setItems((current) => [...current.slice(-3), { id, tone, title, message }]);
      window.setTimeout(() => dismiss(id), 5200);
    },
    [dismiss],
  );

  const value = useMemo(() => ({ notify }), [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      {createPortal(
        <div
          className="pointer-events-none fixed inset-x-0 top-0 z-[100] flex flex-col items-center gap-2 p-4 sm:items-end sm:p-6"
          aria-live="polite"
          aria-atomic="true"
        >
          {items.map((item) => (
            <div
              key={item.id}
              className={clsx(
                "pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-xl border bg-white p-3.5 shadow-lift animate-fade-up",
                item.tone === "success" && "border-emerald-200",
                item.tone === "error" && "border-red-200",
                item.tone === "info" && "border-line",
              )}
            >
              <div
                className={clsx(
                  "mt-0.5 shrink-0",
                  item.tone === "success" && "text-emerald-600",
                  item.tone === "error" && "text-red-600",
                  item.tone === "info" && "text-accent-600",
                )}
              >
                {item.tone === "success" ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : item.tone === "error" ? (
                  <XCircle className="h-4 w-4" />
                ) : (
                  <Info className="h-4 w-4" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-ink-900">{item.title}</p>
                {item.message && <p className="mt-0.5 text-xs leading-5 text-slate-500">{item.message}</p>}
              </div>
              <button
                onClick={() => dismiss(item.id)}
                className="text-slate-400 transition hover:text-slate-700"
                aria-label="Cerrar notificación"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>,
        document.body,
      )}
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const value = useContext(ToastContext);
  if (!value) throw new Error("useToast debe usarse dentro de ToastProvider");
  return value;
}
