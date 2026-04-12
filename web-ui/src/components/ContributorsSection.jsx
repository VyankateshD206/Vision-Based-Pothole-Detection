import { useRef, useState, useEffect } from "react";
import { motion, AnimatePresence, useInView, useReducedMotion } from "motion/react";
import { Link2 as Linkedin, Camera as Instagram, GitBranch as Github, ChevronDown } from "lucide-react";

const contributors = [
    {
        id: 1,
        name: "Atharva Honparkhe",
        avatar: "/contributors/atharva.jpeg",
        fallbackAvatar: "https://avatars.githubusercontent.com/RepoRogue123?v=4",
        accentColor: "#00d4ff",
        roleLabel: "Core Model and UI Developer",
        profileLine: "Led the central model direction and delivered the complete frontend experience from detection flow to insights.",
        oneLiner: "Turns noisy road visuals into sharp ML signals, one edge case at a time.",
        contributions: [
            "Led core severity-model design, feature engineering, and classifier fusion",
            "Built the full UI/UX across detection, insights, and contributor modules",
            "Integrated inference pipeline outputs with end-to-end interactive visualization",
        ],
        social: {
            linkedin: "https://www.linkedin.com/in/atharva-honparkhe-6ba05a2aa/",
            instagram: "https://www.instagram.com/atharva_02_05/",
            github: "https://github.com/RepoRogue123",
        },
    },
    {
        id: 2,
        name: "Vyankatesh Deshpande",
        avatar: "/contributors/Vyankatesh.jpeg",
        fallbackAvatar: "https://avatars.githubusercontent.com/VyankateshD206?v=4",
        accentColor: "#ff6b35",
        roleLabel: "YOLOv8 Segmentation and Data Engineer",
        profileLine: "Focused on dataset preparation and baseline segmentation quality to keep training runs stable and reproducible.",
        oneLiner: "Brings calm engineering and fast iteration to every stage of the pipeline.",
        contributions: [
            "Prepared dataset splits, annotation checks, and preprocessing pipelines",
            "Trained and tuned baseline YOLOv8 segmentation experiments",
            "Managed augmentation and data-quality validation scripts",
        ],
        social: {
            linkedin: "https://www.linkedin.com/in/vyankatesh-deshpande/",
            instagram: "https://www.instagram.com/vyankatesh_206/",
            github: "https://github.com/VyankateshD206",
        },
    },
    {
        id: 3,
        name: "Shashank Parchure",
        avatar: "/contributors/shashank.jpeg",
        fallbackAvatar: "https://avatars.githubusercontent.com/shashankparchure?v=4",
        accentColor: "#a855f7",
        roleLabel: "Data and Evaluation Support",
        profileLine: "Supported segmentation-data workflows and benchmark analysis to improve consistency across experiments.",
        oneLiner: "Keeps the product vision grounded in usability while pushing model quality forward.",
        contributions: [
            "Assisted YOLOv8 mask review and annotation consistency checks",
            "Built evaluation scripts for train/valid/test metric tracking",
            "Supported feature-validation reports and benchmark comparisons",
        ],
        social: {
            linkedin: "https://www.linkedin.com/in/shashank-parchure-360bb6a7/",
            instagram: "https://www.instagram.com/snparchure/",
            github: "https://github.com/shashankparchure",
        },
    },
];

const containerVariants = {
    hidden: {},
    visible: {
        transition: { staggerChildren: 0.08, delayChildren: 0.2 },
    },
};

const itemVariants = {
    hidden: { opacity: 0, y: 14, scale: 0.96 },
    visible: {
        opacity: 1,
        y: 0,
        scale: 1,
        transition: { type: "spring", stiffness: 180, damping: 20 },
    },
};

const nameContainerVariants = {
    hidden: {},
    visible: {
        transition: { staggerChildren: 0.035, delayChildren: 0.06 },
    },
};

const nameCharVariants = {
    hidden: { opacity: 0, y: 12, filter: "blur(3px)" },
    visible: {
        opacity: 1,
        y: 0,
        filter: "blur(0px)",
        transition: { duration: 0.22, ease: "easeOut" },
    },
};

const inViewConfig = { once: true, margin: "-100px" };

const socialPlatforms = [
    { key: "linkedin", label: "LinkedIn", Icon: Linkedin },
    { key: "instagram", label: "Instagram", Icon: Instagram },
    { key: "github", label: "GitHub", Icon: Github },
];

function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

function hexToRgba(hex, alpha) {
    let normalized = hex.replace("#", "").trim();

    if (normalized.length === 3) {
        normalized = normalized
            .split("")
            .map((char) => `${char}${char}`)
            .join("");
    }

    const int = Number.parseInt(normalized, 16);
    const r = (int >> 16) & 255;
    const g = (int >> 8) & 255;
    const b = int & 255;

    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function getInitials(name) {
    return name
        .split(" ")
        .map((part) => part[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();
}

export default function ContributorsSection({ onBackToDetection }) {
    const sectionRef = useRef(null);
    const snapRef = useRef(null);
    const slideRefs = useRef([]);
    const pointerAnimationFrameRef = useRef(null);
    const pointerTargetRef = useRef({ index: -1, x: "50%", y: "50%" });

    const [activeIndex, setActiveIndex] = useState(0);
    const [showShowcase, setShowShowcase] = useState(false);
    const [hoveredSocial, setHoveredSocial] = useState("");
    const [imageLoadState, setImageLoadState] = useState({});
    const prefersReducedMotion = useReducedMotion();

    const sectionInView = useInView(snapRef, { margin: "-100px 0px -100px 0px" });

    useEffect(() => {
        if (!showShowcase) {
            return undefined;
        }

        const container = snapRef.current;
        if (!container) return undefined;

        const updateActiveSlide = () => {
            const slideHeight = container.clientHeight || 1;
            const nextIndex = clamp(
                Math.round(container.scrollTop / slideHeight),
                0,
                contributors.length - 1
            );
            setActiveIndex((current) => (current === nextIndex ? current : nextIndex));
        };

        updateActiveSlide();
        container.addEventListener("scroll", updateActiveSlide, { passive: true });
        window.addEventListener("resize", updateActiveSlide);

        return () => {
            container.removeEventListener("scroll", updateActiveSlide);
            window.removeEventListener("resize", updateActiveSlide);
        };
    }, [showShowcase]);

    useEffect(() => {
        return () => {
            if (pointerAnimationFrameRef.current !== null) {
                window.cancelAnimationFrame(pointerAnimationFrameRef.current);
            }
        };
    }, []);

    const openSocial = (url) => {
        const popup = window.open(url, "_blank", "noopener,noreferrer");
        if (popup) {
            popup.opener = null;
        }
    };

    const scrollToSlide = (index, ensureVisible = false) => {
        const container = snapRef.current;
        if (!container) return;

        const targetTop = index * container.clientHeight;
        container.scrollTo({ top: targetTop, behavior: "smooth" });

        if (ensureVisible) {
            container.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    };

    const handleEnterShowcase = () => {
        if (showShowcase) {
            scrollToSlide(0, true);
            return;
        }

        setShowShowcase(true);
        setActiveIndex(0);

        window.requestAnimationFrame(() => {
            window.requestAnimationFrame(() => {
                const container = snapRef.current;
                if (!container) {
                    return;
                }

                container.scrollTop = 0;
                container.scrollIntoView({ behavior: "smooth", block: "start" });
            });
        });
    };

    const handleBackToDetection = () => {
        setShowShowcase(false);
        setActiveIndex(0);

        if (typeof onBackToDetection === "function") {
            onBackToDetection();
            return;
        }

        const detectionSection = document.getElementById("detection-section");
        if (detectionSection) {
            detectionSection.scrollIntoView({ behavior: "smooth", block: "start" });
            return;
        }

        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    const applyPointerPosition = () => {
        pointerAnimationFrameRef.current = null;
        const { index, x, y } = pointerTargetRef.current;
        const slide = slideRefs.current[index];

        if (!slide) {
            return;
        }

        slide.style.setProperty("--cursor-x", x);
        slide.style.setProperty("--cursor-y", y);
    };

    const queuePointerPosition = (index, x, y) => {
        pointerTargetRef.current = { index, x, y };

        if (pointerAnimationFrameRef.current === null) {
            pointerAnimationFrameRef.current = window.requestAnimationFrame(applyPointerPosition);
        }
    };

    const handleSlidePointerMove = (index, event) => {
        if (prefersReducedMotion || activeIndex !== index) {
            return;
        }

        const rect = event.currentTarget.getBoundingClientRect();
        const x = clamp(((event.clientX - rect.left) / Math.max(rect.width, 1)) * 100, 0, 100);
        const y = clamp(((event.clientY - rect.top) / Math.max(rect.height, 1)) * 100, 0, 100);
        queuePointerPosition(index, `${x}%`, `${y}%`);
    };

    const handleSlidePointerLeave = (index) => {
        if (prefersReducedMotion) {
            return;
        }

        queuePointerPosition(index, "50%", "50%");
    };

    return (
        <section id="contributors" ref={sectionRef} className="relative mt-16 w-full bg-[#0a0f1e] text-[#f9fafb]">
            <style>{`
        @keyframes ringPulse {
          0%, 100% {
            box-shadow: 0 0 0 3px var(--ring-color), 0 0 28px var(--ring-soft);
          }
          50% {
            box-shadow: 0 0 0 6px var(--ring-color), 0 0 42px var(--ring-strong);
          }
        }

        @keyframes teaserGridDrift {
          0% {
            background-position: 0 0, 0 0;
          }
          100% {
            background-position: 0 44px, 44px 0;
          }
        }

        @keyframes teaserScan {
          0% {
            transform: translateY(-40%);
          }
          100% {
            transform: translateY(40%);
          }
        }

        @keyframes ambientGridShift {
          0% {
            background-position: 0 0, 0 0;
          }
          100% {
            background-position: 0 56px, 56px 0;
          }
        }

        @keyframes ambientOrbFloatA {
          0%, 100% {
            transform: translate3d(-2%, -2%, 0) scale(0.98);
            opacity: 0.28;
          }
          50% {
            transform: translate3d(3%, 3%, 0) scale(1.06);
            opacity: 0.42;
          }
        }

        @keyframes ambientOrbFloatB {
          0%, 100% {
            transform: translate3d(2%, 1%, 0) scale(1.04);
            opacity: 0.2;
          }
          50% {
            transform: translate3d(-3%, -3%, 0) scale(0.96);
            opacity: 0.34;
          }
        }

        @keyframes cursorOrbPulse {
          0%, 100% {
            transform: scale(0.96);
            opacity: 0.58;
          }
          50% {
            transform: scale(1.05);
            opacity: 0.84;
          }
        }

        .ring-pulse {
          animation: ringPulse 2.8s ease-in-out infinite;
        }

        .teaser-grid {
          background-image:
            linear-gradient(to bottom, rgba(31, 41, 55, 0.28) 1px, transparent 1px),
            linear-gradient(to right, rgba(31, 41, 55, 0.28) 1px, transparent 1px);
          background-size: 44px 44px;
          animation: teaserGridDrift 12s linear infinite;
        }

        .teaser-scan::after {
          content: "";
          position: absolute;
          left: 0;
          right: 0;
          height: 36%;
          background: linear-gradient(
            to bottom,
            rgba(0, 212, 255, 0),
            rgba(0, 212, 255, 0.06),
            rgba(0, 212, 255, 0)
          );
          animation: teaserScan 5s ease-in-out infinite alternate;
        }

        .ambient-grid {
          background-image:
            linear-gradient(to bottom, var(--grid-line) 1px, transparent 1px),
            linear-gradient(to right, var(--grid-line) 1px, transparent 1px);
          background-size: 56px 56px;
          opacity: 0.42;
          will-change: background-position, opacity;
          transition: opacity 260ms ease;
        }

        .ambient-grid-active {
          animation: ambientGridShift 14s linear infinite;
          opacity: 0.62;
        }

        .ambient-orb {
          will-change: transform, opacity;
          transform: translateZ(0);
          transition: opacity 260ms ease;
        }

        .ambient-orb-a {
          animation: ambientOrbFloatA 8.5s ease-in-out infinite;
        }

        .ambient-orb-b {
          animation: ambientOrbFloatB 11s ease-in-out infinite;
        }

        .cursor-orb-layer {
          background-image:
            radial-gradient(
                                                        560px circle at var(--cursor-x, 50%) var(--cursor-y, 50%),
              var(--cursor-strong),
              rgba(10, 15, 30, 0) 66%
            ),
            radial-gradient(
                                                        420px circle at calc(var(--cursor-x, 50%) + 8%) calc(var(--cursor-y, 50%) - 6%),
              var(--cursor-soft),
              rgba(10, 15, 30, 0) 68%
            );
          mix-blend-mode: screen;
          opacity: 0;
          transition: opacity 220ms ease;
          will-change: opacity, transform;
        }

        .cursor-orb-active {
          animation: cursorOrbPulse 4s ease-in-out infinite;
          opacity: 0.86;
        }
      `}</style>

            <div className="relative h-[20vh] min-h-[180px] w-full overflow-hidden border-y border-[#1f2937] bg-[#0a0f1e]">
                <div className="teaser-grid pointer-events-none absolute inset-0 opacity-60" />
                <div className="teaser-scan pointer-events-none absolute inset-0" />

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={inViewConfig}
                    transition={{ type: "spring", stiffness: 90, damping: 20 }}
                    className="relative z-10 flex h-full flex-col items-center justify-center px-4 text-center"
                >
                    <h2
                        className="text-3xl font-black tracking-tight sm:text-4xl"
                        style={{
                            backgroundImage: "linear-gradient(90deg, #00d4ff 0%, #a855f7 100%)",
                            WebkitBackgroundClip: "text",
                            backgroundClip: "text",
                            color: "transparent",
                        }}
                    >
                        The Minds Behind the Model
                    </h2>

                    <motion.button
                        type="button"
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={handleEnterShowcase}
                        className="mt-3 rounded-full border border-[#1f2937] bg-[#111827]/85 px-4 py-1.5 text-xs font-semibold tracking-wider text-[#f9fafb]"
                        style={{ boxShadow: "0 0 0 1px rgba(0, 212, 255, 0.25), 0 0 24px rgba(0, 212, 255, 0.18)" }}
                    >
                        Enter Team Showcase
                    </motion.button>

                    <motion.div
                        animate={
                            prefersReducedMotion
                                ? { opacity: 0.85 }
                                : { y: [0, 7, 0], opacity: [0.65, 1, 0.65] }
                        }
                        transition={
                            prefersReducedMotion
                                ? { duration: 0.2 }
                                : { repeat: Infinity, duration: 1.8, ease: "easeInOut" }
                        }
                        className="mt-2"
                    >
                        <ChevronDown className="h-5 w-5 text-[#00d4ff]" />
                    </motion.div>
                </motion.div>
            </div>

            {showShowcase && (
                <div
                    ref={snapRef}
                    className="relative h-screen max-h-screen snap-y snap-mandatory overflow-y-scroll overscroll-y-contain"
                >
                    {contributors.map((contributor, index) => {
                        const accent = contributor.accentColor;
                        const accent10 = hexToRgba(accent, 0.1);
                        const accent14 = hexToRgba(accent, 0.14);
                        const accent15 = hexToRgba(accent, 0.15);
                        const accentSoft = hexToRgba(accent, 0.24);
                        const accentStrong = hexToRgba(accent, 0.34);
                        const isActive = activeIndex === index;
                        const avatarState = imageLoadState[contributor.id] || "primary";
                        const avatarSrc = avatarState === "primary" ? contributor.avatar : contributor.fallbackAvatar;

                        return (
                            <section
                                key={contributor.id}
                                className="relative h-screen snap-start overflow-hidden"
                                style={{
                                    backgroundColor: "#0a0f1e",
                                    "--grid-line": hexToRgba(accent, 0.08),
                                    "--cursor-x": "50%",
                                    "--cursor-y": "50%",
                                    "--cursor-soft": hexToRgba(accent, 0.15),
                                    "--cursor-strong": hexToRgba(accent, 0.32),
                                }}
                                ref={(node) => {
                                    slideRefs.current[index] = node;
                                }}
                                onPointerMove={(event) => handleSlidePointerMove(index, event)}
                                onPointerLeave={() => handleSlidePointerLeave(index)}
                            >
                                <div
                                    className={`pointer-events-none absolute inset-0 ambient-grid ${isActive && !prefersReducedMotion ? "ambient-grid-active" : ""
                                        }`}
                                    style={{
                                        opacity: isActive ? 0.62 : 0.34,
                                    }}
                                />

                                <div
                                    className={`pointer-events-none absolute -left-14 top-1/4 h-64 w-64 rounded-full blur-3xl ambient-orb ${!prefersReducedMotion ? "ambient-orb-a" : ""
                                        }`}
                                    style={{
                                        background: `radial-gradient(circle, ${hexToRgba(accent, 0.3)} 0%, transparent 70%)`,
                                        opacity: isActive ? 0.36 : 0.16,
                                    }}
                                />

                                <div
                                    className={`pointer-events-none absolute -right-32 top-1/2 h-[34rem] w-[34rem] -translate-y-1/2 rounded-full blur-[110px] ambient-orb ${!prefersReducedMotion ? "ambient-orb-b" : ""
                                        }`}
                                    style={{
                                        background: `radial-gradient(circle, ${hexToRgba(accent, 0.24)} 0%, transparent 72%)`,
                                        opacity: isActive ? 0.3 : 0.14,
                                    }}
                                />

                                <div
                                    className={`pointer-events-none absolute inset-0 cursor-orb-layer ${isActive && !prefersReducedMotion ? "cursor-orb-active" : ""
                                        }`}
                                />

                                <div
                                    className="absolute inset-0"
                                    style={{
                                        backgroundImage: `
                    radial-gradient(circle at 76% 38%, ${hexToRgba(accent, 0.08)} 0%, rgba(10, 15, 30, 0) 56%),
                    repeating-linear-gradient(-32deg, rgba(249, 250, 251, 0.022) 0px, rgba(249, 250, 251, 0.022) 1px, rgba(10, 15, 30, 0) 1px, rgba(10, 15, 30, 0) 24px)
                  `,
                                    }}
                                />

                                <div className="relative z-10 mx-auto h-full max-w-[88rem] px-6 py-8 md:px-10">
                                    <motion.span
                                        initial={{ opacity: 0, y: -12 }}
                                        whileInView={{ opacity: 1, y: 0 }}
                                        viewport={inViewConfig}
                                        transition={{ delay: 0.04 }}
                                        className="absolute right-6 top-6 rounded-full border border-[#1f2937] bg-[#111827]/75 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#9ca3af]"
                                        style={{ boxShadow: `0 0 16px ${hexToRgba(accent, 0.12)}` }}
                                    >
                                        Slide {index + 1} / {contributors.length}
                                    </motion.span>

                                    <div className="grid h-full grid-cols-1 items-center gap-8 md:grid-cols-[1.22fr_0.78fr] md:gap-10 lg:gap-14">
                                        <div className="relative flex flex-col items-center gap-6 text-center md:items-start md:text-left">
                                            <span
                                                className="pointer-events-none absolute -top-8 left-1/2 -translate-x-1/2 select-none text-[7rem] font-black leading-none md:-top-12 md:left-0 md:translate-x-0 md:text-[10rem]"
                                                style={{ color: accent15 }}
                                            >
                                                {String(index + 1).padStart(2, "0")}
                                            </span>

                                            <motion.h3
                                                key={`name-${contributor.id}-${activeIndex === index ? "active" : "idle"}`}
                                                variants={nameContainerVariants}
                                                initial="hidden"
                                                animate={activeIndex === index ? "visible" : "hidden"}
                                                className="relative z-10 max-w-full whitespace-nowrap text-[clamp(1.2rem,5.2vw,1.8rem)] font-black leading-[1.04] tracking-tight text-white sm:text-[clamp(1.95rem,3.9vw,3rem)] lg:text-[clamp(2.25rem,3vw,3.45rem)]"
                                            >
                                                {prefersReducedMotion
                                                    ? contributor.name
                                                    : contributor.name.split("").map((character, charIndex) => (
                                                        <motion.span
                                                            key={`${contributor.id}-char-${charIndex}`}
                                                            variants={nameCharVariants}
                                                            className="inline-block"
                                                        >
                                                            {character === " " ? "\u00A0" : character}
                                                        </motion.span>
                                                    ))}
                                            </motion.h3>

                                            <motion.span
                                                initial={{ opacity: 0, x: -22 }}
                                                whileInView={{ opacity: 1, x: 0 }}
                                                viewport={inViewConfig}
                                                transition={{ delay: 0.2 }}
                                                className="relative z-10 inline-flex rounded-full border px-4 py-1 text-sm font-semibold"
                                                style={{
                                                    borderColor: accent,
                                                    color: accent,
                                                    backgroundColor: accent10,
                                                }}
                                            >
                                                {contributor.roleLabel}
                                            </motion.span>

                                            <motion.p
                                                initial={{ opacity: 0, x: -20 }}
                                                whileInView={{ opacity: 1, x: 0 }}
                                                viewport={inViewConfig}
                                                transition={{ delay: 0.3 }}
                                                className="relative z-10 max-w-2xl text-[1.05rem] leading-relaxed text-[#d1d5db]"
                                            >
                                                {contributor.profileLine}
                                            </motion.p>

                                            <motion.div
                                                variants={containerVariants}
                                                initial="hidden"
                                                whileInView="visible"
                                                viewport={inViewConfig}
                                                className="relative z-10 mt-2 flex flex-wrap items-center justify-center gap-3 md:justify-start"
                                            >
                                                {socialPlatforms.map(({ key, label, Icon }) => {
                                                    const socialKey = `${contributor.id}-${key}`;
                                                    const isHovered = hoveredSocial === socialKey;

                                                    return (
                                                        <motion.div
                                                            key={socialKey}
                                                            variants={itemVariants}
                                                            whileHover={{ scale: 1.12 }}
                                                            whileTap={{ scale: 0.95 }}
                                                            onMouseEnter={() => setHoveredSocial(socialKey)}
                                                            onMouseLeave={() => setHoveredSocial("")}
                                                            onClick={() => openSocial(contributor.social[key])}
                                                            className="relative cursor-pointer rounded-xl border p-3"
                                                            style={{
                                                                borderColor: "#1f2937",
                                                                backgroundColor: isHovered ? accent14 : "#111827",
                                                                boxShadow: isHovered ? `0 0 20px ${accentSoft}` : "none",
                                                                transition: "background-color 160ms ease, box-shadow 160ms ease",
                                                            }}
                                                            aria-label={`${label} profile for ${contributor.name}`}
                                                            role="button"
                                                            tabIndex={0}
                                                            onKeyDown={(event) => {
                                                                if (event.key === "Enter" || event.key === " ") {
                                                                    event.preventDefault();
                                                                    openSocial(contributor.social[key]);
                                                                }
                                                            }}
                                                        >
                                                            <Icon className="h-4 w-4 text-[#f9fafb]" />

                                                            <AnimatePresence>
                                                                {isHovered && (
                                                                    <motion.div
                                                                        initial={{ opacity: 0, y: 8 }}
                                                                        animate={{ opacity: 1, y: 0 }}
                                                                        exit={{ opacity: 0, y: 8 }}
                                                                        className="pointer-events-none absolute -top-9 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md border border-[#1f2937] bg-[#111827] px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-[#f9fafb]"
                                                                    >
                                                                        {label}
                                                                    </motion.div>
                                                                )}
                                                            </AnimatePresence>
                                                        </motion.div>
                                                    );
                                                })}
                                            </motion.div>
                                        </div>

                                        <motion.div
                                            initial={{ opacity: 0, x: 44, scale: 0.9 }}
                                            whileInView={{ opacity: 1, x: 0, scale: 1 }}
                                            viewport={inViewConfig}
                                            transition={{ type: "spring", stiffness: 80, damping: 18, delay: 0.12 }}
                                            className="flex flex-col items-center justify-center gap-5 md:gap-6"
                                        >
                                            <div
                                                className={`relative rounded-full p-3 ${isActive && !prefersReducedMotion ? "ring-pulse" : ""
                                                    }`}
                                                style={{
                                                    "--ring-color": accent,
                                                    "--ring-soft": accentSoft,
                                                    "--ring-strong": accentStrong,
                                                    boxShadow:
                                                        isActive || prefersReducedMotion
                                                            ? `0 0 0 2px ${accent}, 0 0 24px ${hexToRgba(accent, 0.2)}`
                                                            : `0 0 0 1px ${accent}`,
                                                }}
                                            >
                                                {avatarState !== "failed" ? (
                                                    <img
                                                        src={avatarSrc}
                                                        alt={contributor.name}
                                                        className="h-64 w-64 rounded-full object-cover md:h-72 md:w-72"
                                                        onError={() => {
                                                            setImageLoadState((current) => {
                                                                const currentState = current[contributor.id] || "primary";

                                                                if (currentState === "primary") {
                                                                    return {
                                                                        ...current,
                                                                        [contributor.id]: "fallback",
                                                                    };
                                                                }

                                                                if (currentState === "fallback") {
                                                                    return {
                                                                        ...current,
                                                                        [contributor.id]: "failed",
                                                                    };
                                                                }

                                                                return current;
                                                            });
                                                        }}
                                                    />
                                                ) : (
                                                    <div
                                                        className="flex h-64 w-64 items-center justify-center rounded-full border-2 text-5xl font-black md:h-72 md:w-72"
                                                        style={{
                                                            borderColor: accent,
                                                            color: accent,
                                                            backgroundColor: "#111827",
                                                        }}
                                                    >
                                                        {getInitials(contributor.name)}
                                                    </div>
                                                )}
                                            </div>

                                            <div className="w-full max-w-xl rounded-2xl border border-[#1f2937] bg-[#0f172a]/75 p-5 text-left">
                                                <blockquote
                                                    className="mt-3 border-l-2 pl-4 text-[1.02rem] font-medium leading-relaxed text-[#e5e7eb]"
                                                    style={{ borderColor: accent }}
                                                >
                                                    "{contributor.oneLiner}"
                                                </blockquote>
                                                <cite className="mt-3 block text-sm font-semibold not-italic" style={{ color: accent }}>
                                                    - {contributor.name}
                                                </cite>

                                                <div className="mt-4 border-t border-[#1f2937] pt-4">
                                                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#9ca3af]">
                                                        Contributions
                                                    </p>

                                                    <div className="mt-2 flex flex-wrap gap-2">
                                                        {contributor.contributions.map((item) => (
                                                            <span
                                                                key={`${contributor.id}-${item}`}
                                                                className="rounded-full border border-[#1f2937] bg-[#111827]/70 px-3 py-1 text-xs font-medium text-[#d1d5db]"
                                                            >
                                                                {item}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>
                                    </div>
                                </div>
                            </section>
                        );
                    })}
                </div>
            )}

            <AnimatePresence>
                {showShowcase && (
                    <>
                        <motion.button
                            type="button"
                            initial={{ opacity: 0, x: -16 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -16 }}
                            onClick={handleBackToDetection}
                            className="fixed bottom-6 left-6 z-50 rounded-full border border-[#1f2937] bg-[#111827]/90 px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#f9fafb]"
                            style={{ boxShadow: "0 0 0 1px rgba(0, 212, 255, 0.3), 0 0 18px rgba(0, 212, 255, 0.2)" }}
                            whileHover={{ scale: 1.04 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            Back to Detection
                        </motion.button>

                        <motion.div
                            initial={{ opacity: 0, x: 16 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 16 }}
                            className="fixed right-6 top-1/2 z-50 -translate-y-1/2"
                        >
                            <div className="flex flex-col gap-3">
                                {contributors.map((contributor, index) => {
                                    const isActive = activeIndex === index;

                                    return (
                                        <motion.div
                                            key={`dot-${contributor.id}`}
                                            className="h-2 w-2 rounded-full"
                                            role="button"
                                            tabIndex={0}
                                            onClick={() => scrollToSlide(index)}
                                            onKeyDown={(event) => {
                                                if (event.key === "Enter" || event.key === " ") {
                                                    event.preventDefault();
                                                    scrollToSlide(index);
                                                }
                                            }}
                                            style={{ cursor: "pointer" }}
                                            animate={{
                                                scale: isActive ? 1.5 : 1,
                                                backgroundColor: isActive ? contributor.accentColor : "#374151",
                                                boxShadow: isActive ? `0 0 8px ${contributor.accentColor}` : "0 0 0px transparent",
                                            }}
                                            transition={{ type: "spring", stiffness: 220, damping: 22 }}
                                        />
                                    );
                                })}
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </section>
    );
}