import clsx from "clsx";

export function Logo({
  size = 38,
  className,
  showWordmark = false,
  light = false,
}: {
  size?: number;
  className?: string;
  showWordmark?: boolean;
  light?: boolean;
}) {
  return (
    <div className={clsx("flex items-center gap-3", className)}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 64 64"
        role="img"
        aria-label="CIS Hardening Auditor"
        className="shrink-0 drop-shadow-[0_4px_18px_rgba(6,182,212,0.28)]"
      >
        <defs>
          <linearGradient id="shieldGradient" x1="8" y1="4" x2="56" y2="60" gradientUnits="userSpaceOnUse">
            <stop stopColor="#22D3EE" />
            <stop offset="1" stopColor="#0891B2" />
          </linearGradient>
        </defs>
        <rect width="64" height="64" rx="17" fill="#0B1220" />
        <path
          d="M32 9.5 50 17v13.1c0 11.1-7.2 19.6-18 24.4-10.8-4.8-18-13.3-18-24.4V17l18-7.5Z"
          fill="url(#shieldGradient)"
        />
        <path
          d="m23 32.4 6 6.2 12-12.5"
          fill="none"
          stroke="#06121F"
          strokeWidth="4.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {showWordmark && (
        <div className="min-w-0">
          <p className={clsx("truncate text-sm font-bold tracking-tight", light ? "text-white" : "text-ink-950")}>
            CIS Hardening
          </p>
          <p className={clsx("text-[10px] font-semibold uppercase tracking-[0.2em]", light ? "text-cyan-300/80" : "text-accent-700")}>
            Auditor
          </p>
        </div>
      )}
    </div>
  );
}
