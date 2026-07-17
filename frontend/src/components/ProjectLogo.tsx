import { DESMOS_INNER_PATHS } from "../assets/desmosInnerPaths";

interface ProjectLogoProps {
  className?: string;
  labelled?: boolean;
}

export function ProjectLogo({
  className,
  labelled = false,
}: ProjectLogoProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 480 480"
      role={labelled ? "img" : undefined}
      aria-label={labelled ? "PlantDiseaseAI" : undefined}
      aria-hidden={labelled ? undefined : "true"}
    >
      <defs>
        <linearGradient
          id="plant-logo-fill"
          x1="84"
          y1="72"
          x2="392"
          y2="408"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0" stopColor="#c4eaff" />
          <stop offset="0.48" stopColor="#b2ebca" />
          <stop offset="1" stopColor="#48a879" />
        </linearGradient>
        <linearGradient
          id="plant-logo-line"
          x1="112"
          y1="132"
          x2="372"
          y2="332"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0" stopColor="#ffffff" stopOpacity="0.96" />
          <stop offset="1" stopColor="#1f7652" stopOpacity="0.9" />
        </linearGradient>
        <clipPath id="plant-logo-clip">
          <path d="M404 58C225 65 113 153 124 326c78 52 199 25 250-74 29-57 35-126 30-194Z" />
        </clipPath>
      </defs>
      <path
        data-logo-layer="leaf"
        d="M404 58C225 65 113 153 124 326c78 52 199 25 250-74 29-57 35-126 30-194Z"
        fill="url(#plant-logo-fill)"
        stroke="#247653"
        strokeWidth="8"
        strokeLinejoin="round"
      />
      <path
        d="M102 398C171 291 245 218 350 145"
        fill="none"
        stroke="#ffffff"
        strokeOpacity="0.72"
        strokeWidth="11"
        strokeLinecap="round"
      />
      <g
        data-logo-layer="desmos-gesture"
        clipPath="url(#plant-logo-clip)"
        fill="none"
        stroke="url(#plant-logo-line)"
        strokeWidth="8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {DESMOS_INNER_PATHS.map(([id, d]) => (
          <path key={id} data-source-path={id} d={d} />
        ))}
      </g>
      <path
        d="M170 112c57-34 132-46 194-38"
        fill="none"
        stroke="#ffffff"
        strokeOpacity="0.52"
        strokeWidth="9"
        strokeLinecap="round"
      />
    </svg>
  );
}
