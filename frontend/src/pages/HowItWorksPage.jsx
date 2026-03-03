import { useCallback, useEffect, useRef, useState } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import Navbar from "@/components/Navbar";

const STEPS = [
  {
    number: "01",
    title: "EIA API",
    subtitle: "Energy Information Administration",
    body: "We pull live grid data from the U.S. Energy Information Administration for 13 regional electricity markets. For each region, we collect hourly electricity demand, fuel mix (solar, wind, nuclear, gas, etc.), and real-time electricity prices.",
    image: { src: "/images/eia-logo.png", alt: "EIA logo" },
  },
  {
    number: "02",
    title: "Open-Meteo",
    subtitle: "Weather & Climate Data",
    body: "Temperature is a key factor in data center efficiency — cooling costs rise sharply in hot climates. We fetch a 60-day mean temperature for each region's geographic coordinates from Open-Meteo's free forecast API.",
    image: { src: "/images/open-meteo-logo.png", alt: "Open-Meteo logo" }
  },
  {
    number: "03",
    title: "AWS Fargate",
    subtitle: "Serverless Pipeline Execution",
    body: "A containerized Python pipeline runs daily on AWS Fargate — no servers to manage. EventBridge triggers the container each morning, it fetches all data sources in sequence, computes scores, and uploads the results to S3.",
    image: { src: "/images/aws-logo.png", alt: "AWS logo" }
  },
  {
    number: "04",
    title: "GridAsk",
    subtitle: "AI-Powered Grid Intelligence",
    body: "GridAsk is an OpenAI-powered assistant built on top of the GridScore data. Ask it anything about the grid — which regions are cheapest right now, where renewable energy is peaking, or how conditions compare across markets. It interprets the data and answers in plain language.",
    image: { src: "/images/OpenAI-logo.png", alt: "GridAsk logo" }
  },
  {
    number: "05",
    title: "GridCast Frontend",
    subtitle: "Interactive Hex Map on Vercel",
    body: "The React + Mapbox frontend fetches the latest score JSON from S3 and renders it as an interactive H3 hex grid. Users can switch between metrics, hover for details, and compare any two hexagons side-by-side.",
    image: { src: "/images/vercel-logo.png", alt: "vercel logo" },
  },
];

function TimelineStep({ step, index, isLast, dotRef }) {
  const isLeft = index % 2 === 0;
  const hasImage = Boolean(step.image?.src);

  const card = (
    <motion.div
      className="w-full max-w-sm bg-glass border border-white/10 backdrop-blur-md rounded-2xl px-7 py-6 shadow-[0_0_20px_rgba(0,255,128,0.07)]"
      initial={{ opacity: 0, x: isLeft ? -40 : 40 }}
      whileInView={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.7, ease: "easeOut" }}
      viewport={{ once: true, margin: "-80px" }}
    >
      <p className="text-xs font-mono text-neon mb-1 tracking-widest">{step.number}</p>
      <h3 className="text-lg font-bold text-white">{step.title}</h3>
      <p className="text-xs text-neon/70 mb-3 font-medium">{step.subtitle}</p>
      <p className="text-sm text-white/65 leading-relaxed">{step.body}</p>
    </motion.div>
  );

  const dot = (
    <motion.div
      ref={dotRef}
      className="flex-none z-10 w-4 h-4 rounded-full bg-neon shadow-[0_0_14px_rgba(0,255,128,0.9)]"
      initial={{ scale: 0, opacity: 0 }}
      whileInView={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      viewport={{ once: true, margin: "-60px" }}
    />
  );

  const media = hasImage ? (
    <motion.div
      className="w-full max-w-sm flex items-center justify-center"
      initial={{ opacity: 0, x: isLeft ? 40 : -40 }}
      whileInView={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.7, ease: "easeOut" }}
      viewport={{ once: true, margin: "-80px" }}
    >
      <img
        src={step.image.src}
        alt={step.image.alt ?? `${step.title} logo`}
        className="block max-h-52 md:max-h-64 w-auto max-w-full object-contain"
      />
    </motion.div>
  ) : null;

  if (isLast) {
    return (
      <div>
        <div className="flex items-center">
          <div className="flex-1 flex justify-end pr-10">
            {isLeft ? card : media}
          </div>
          <div className="flex-none w-4" />
          <div className="flex-1 flex justify-start pl-10">
            {!isLeft ? card : media}
          </div>
        </div>
        <div className="flex justify-center mt-6">
          {dot}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center">
      <div className="flex-1 flex justify-end pr-10">
        {isLeft ? card : media}
      </div>
      {dot}
      <div className="flex-1 flex justify-start pl-10">
        {!isLeft ? card : media}
      </div>
    </div>
  );
}

export default function HowItWorksPage() {
  const timelineRef = useRef(null);
  const firstDotRef = useRef(null);
  const lastDotRef = useRef(null);
  const [lineBounds, setLineBounds] = useState({ top: 0, height: 0 });

  const measureLineBounds = useCallback(() => {
    if (!timelineRef.current || !firstDotRef.current || !lastDotRef.current) return;

    const timelineRect = timelineRef.current.getBoundingClientRect();
    const firstDotRect = firstDotRef.current.getBoundingClientRect();
    const lastDotRect = lastDotRef.current.getBoundingClientRect();

    const top = firstDotRect.top + firstDotRect.height / 2 - timelineRect.top;
    const bottom = lastDotRect.top + lastDotRect.height / 2 - timelineRect.top;
    const height = Math.max(bottom - top, 0);

    setLineBounds((prev) => (
      prev.top === top && prev.height === height ? prev : { top, height }
    ));
  }, []);

  useEffect(() => {
    const raf = requestAnimationFrame(measureLineBounds);
    window.addEventListener("resize", measureLineBounds);

    const observer = new ResizeObserver(measureLineBounds);
    if (timelineRef.current) observer.observe(timelineRef.current);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", measureLineBounds);
      observer.disconnect();
    };
  }, [measureLineBounds]);

  const { scrollYProgress } = useScroll({
    target: timelineRef,
    offset: ["start 80%", "end end"],
  });

  const lineScaleY = useTransform(scrollYProgress, [0, 1], [0, 1]);

  return (
    <div className="min-h-screen bg-dark-bg text-white">
      <Navbar />

      {/* Hero */}
      <section className="pt-40 pb-16 px-6 text-center">
        <motion.p
          className="text-xs font-mono text-neon tracking-widest mb-4"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          THE PIPELINE
        </motion.p>
        <motion.h1
          className="text-5xl md:text-6xl font-bold tracking-tight text-white mb-5"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
        >
          How It Works
        </motion.h1>
        <motion.p
          className="text-white/55 text-lg max-w-xl mx-auto leading-relaxed"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
        >
          GridCast pulls real-time energy data from government and weather APIs,
          runs a daily scoring pipeline on AWS, and delivers the results as an
          interactive map.
        </motion.p>
      </section>

      {/* Timeline — section ends at last dot so the line naturally terminates there */}
      <section className="relative max-w-4xl mx-auto px-6" ref={timelineRef}>
        {/* Track line (gray) */}
        <div
          className="absolute left-1/2 -translate-x-px w-px bg-white/10"
          style={{ top: lineBounds.top, height: lineBounds.height }}
        />

        {/* Animated fill line (neon green) */}
        <motion.div
          className="absolute left-1/2 -translate-x-px w-px bg-neon origin-top shadow-[0_0_8px_rgba(0,255,128,0.6)]"
          style={{ top: lineBounds.top, height: lineBounds.height, scaleY: lineScaleY }}
        />

        {/* Steps — no bottom padding so section ends at the last dot */}
        <div className="flex flex-col gap-20 pt-8">
          {STEPS.map((step, i) => (
            <TimelineStep
              key={step.number}
              step={step}
              index={i}
              isLast={i === STEPS.length - 1}
              dotRef={
                i === 0
                  ? firstDotRef
                  : i === STEPS.length - 1
                    ? lastDotRef
                    : undefined
              }
            />
          ))}
        </div>
      </section>

      {/* CTA footer */}
      <section className="mt-24 pb-32 px-6 text-center">
        <motion.div
          className="max-w-lg mx-auto bg-glass border border-white/10 backdrop-blur-md rounded-3xl px-10 py-12 shadow-[0_0_40px_rgba(0,255,128,0.08)]"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          viewport={{ once: true, margin: "-60px" }}
        >
          <p className="text-xs font-mono text-neon tracking-widest mb-4">READY TO EXPLORE</p>
          <h2 className="text-3xl font-bold text-white mb-4 tracking-tight">
            See it in action
          </h2>
          <p className="text-white/55 text-sm leading-relaxed mb-8">
            The pipeline runs daily. Open the dashboard to explore GridScores
            across every U.S. grid region, compare hexagons, and drill into the
            underlying signals.
          </p>
          <a
            href="/dashboard"
            className="inline-block rounded-full bg-neon px-8 py-3 text-sm font-semibold text-black transition hover:brightness-110 hover:shadow-[0_0_20px_rgba(0,255,128,0.5)]"
          >
            Launch Dashboard →
          </a>
        </motion.div>
      </section>
    </div>
  );
}
