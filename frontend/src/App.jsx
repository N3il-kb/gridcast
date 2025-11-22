import { motion } from "framer-motion";
import Dither from "@/components/Dither";
import Navbar from "@/components/Navbar";

const sections = [
  {
    id: "datacenters",
    title: "What Are Datacenters?",
    text: `Every search, every AI query, every cloud upload — they all run through datacenters.
These massive facilities house thousands of servers that process, store, and transmit data around the clock.
In essence, datacenters are the factories of the digital era — the invisible engines powering everything from Netflix to GPT.`,
    background: "/images/datacenter-bg.jpg",
  },
  {
    id: "future",
    title: "Energy concerns of data centers",
    text: `Artificial intelligence is revolutionizing every industry from healthcare to finance, and its growth shows no signs of slowing. 
    But behind every query and every AI model training session lies massive computational infrastructure. Data centers currently consume 1-2% of global electricity, 
    and with AI's explosive growth, that number is skyrocketing.The energy used to power these data centers must be monitored and optimized to fit our needs as businesses and as people. 
    As AI becomes more integrated into our daily lives, we're facing a critical question: how do we fuel this technological revolution without accelerating the climate crisis?
`,
    background: "/images/coal-bg.jpg",
  },
  {
    id: "energy",
    title: "What are sustainable data centers",
    text: `“Sustainable data centers are facilities designed to minimize environmental impact while maintaining high computing performance. 
    These facilities achieve efficiency through renewable energy sources, optimized cooling systems with low PUE ratings, water conservation, and circular economy practices like hardware recycling.
    The best sustainable data centers can operate on 100% renewable energy with PUE scores below 1.15, compared to the industry average of 1.58.`,
    background: "/images/sustainable_datacenter.jpg",
  },
  {
    id: "score",
    title: "Introducing the Datacenter Score",
    text: `GridScore.
To measure the concerns of this growing industry, we developed GridScore—a comprehensive dual-framework that evaluates data centers on both ESG performance and profitability using a 60/40 weighting system.
The ESG component (60%) measures environmental factors like energy efficiency and renewable usage, social factors like worker safety and community impact, and governance factors like transparency and cybersecurity. 
The profitability component (40%) assesses operational efficiency, revenue quality, capital efficiency, and market position, ensuring that sustainable facilities are also financially viable.`,
    background: "/images/hex-bg.jpg",
  },
  {
    id: "sustainability",
    title: "Sustainability and Custom Scores",
    text: `Every company can define its own sustainability priorities — whether minimizing carbon footprint, maximizing uptime, or balancing both.
GridCast allows you to create a Custom Sustainability Score, blending renewable energy intensity, carbon cost, and operational metrics unique to your datacenter.`,
    background: "/images/sustainability-bg.jpg",
  },
  {
    id: "gridcast",
    title: "What Is GridCast?",
    text: `Our mission is to use data to provide this information on how and where to build the perfect data center. We believe there is a smarter and better way to ride the wave of AI without harming the planet in the process. 
    Welcome to GridCast.`,
    background: "/images/hex-gr-bg.avif",
    showLaunchButton: true,
  },
];

export default function App() {
  return (
    <main className="relative flex min-h-screen w-full flex-col items-center justify-start overflow-x-hidden bg-black text-white">
      {/* Navbar */}
      <Navbar />

      {/* Hero Section */}
      <section className="relative isolate z-10 flex min-h-[100vh] w-full flex-col items-center overflow-hidden px-4 pb-10">
        <div className="absolute inset-0 -z-10">
          <Dither
            className="pointer-events-none"
            waveColor={[0.5, 0.7, 0.5]}
            disableAnimation={false}
            enableMouseInteraction={false}
            mouseRadius={0.3}
            colorNum={6.7}
            waveAmplitude={0}
            waveFrequency={0}
            waveSpeed={0.01}
          />
        </div>

        <div className="relative z-10 flex w-full max-w-5xl flex-1 flex-col items-center justify-center text-center">
          <h1 className="text-5xl sm:text-7xl font-extrabold tracking-tight text-white drop-shadow-[0_0_15px_rgba(0,255,128,0.25)] mt-36">
            ⚡️GridCast
      </h1>
      <p className="mt-4 max-w-2xl text-lg text-white/80 sm:text-xl">
        Forecasting the energy of tomorrow, today.
      </p>

      <div className="mt-8 flex flex-col gap-4 sm:flex-row">
        <a
          href="/hex_map.html"
          className="px-8 py-3 rounded-full border border-white/60 bg-white text-black font-semibold hover:bg-green-400/20 hover:text-white transition-all text-center"
        >
          Launch Dashboard
        </a>
        <button className="px-8 py-3 rounded-full border border-white/20 bg-white/5 text-white/80 font-medium hover:bg-white/10 transition-all">
          Learn More
        </button>
      </div>
        </div>

        <div className="relative z-10 mt-12 w-full max-w-6xl text-center">
          <div className="grid w-full grid-cols-1 gap-6 sm:grid-cols-3">
            <FeatureCard
              title="Real-Time Insights"
              text="Live data visualizations of regional and national energy grids to stay ahead of market shifts."
            />
            <FeatureCard
              title="AI Forecasting"
              text="Powered by advanced ARIMA + neural hybrid models for accurate energy demand predictions."
            />
            <FeatureCard
              title="Sustainability Index"
              text="Balance profitability and sustainability with our datacenter and ESG scoring models."
            />
          </div>
        </div>
      </section>

      {/* Presentation Narrative Sections */}
      <div className="w-full">
        {sections.map((section, i) => (
          <FullScreenSection key={section.id} {...section} />
        ))}
      </div>
    </main>
  );
}

function FeatureCard({ title, text }) {
  return (
    <div className="rounded-2xl bg-white/5 border border-white/10 p-6 backdrop-blur-md text-center hover:bg-white/10 transition">
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-white/70">{text}</p>
    </div>
  );
}

function FullScreenSection({ title, text, background, showLaunchButton }) {
  return (
    <section className="relative isolate flex h-screen items-center justify-center overflow-hidden px-6 text-center md:px-24">
      {background ? (
        <motion.div
          aria-hidden="true"
          className="absolute inset-0 z-0 bg-cover bg-center"
          style={{ backgroundImage: `url(${background})` }}
          initial={{ scale: 1.05, opacity: 0.6 }}
          whileInView={{ scale: 1, opacity: 0.95 }}
          transition={{ duration: 1.2, ease: "easeOut" }}
          viewport={{ once: true }}
        />
      ) : (
        <div className="absolute inset-0 z-0 bg-black" aria-hidden="true" />
      )}

      {/* Soft gradient overlay to keep text legible */}
      <motion.div
        className="absolute inset-0 z-20 bg-gradient-to-b from-black/15 via-black/45 to-black/85 backdrop-blur-[1px]"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        transition={{ duration: 1 }}
        viewport={{ once: true }}
      />

      {/* Floating color mist effect */}
      <motion.div
        className="absolute inset-[-10%] z-10 h-[120%] w-[120%] animate-pulse bg-gradient-to-tr from-green-400/12 via-blue-500/12 to-purple-600/12 blur-3xl"
        initial={{ scale: 1 }}
        animate={{ scale: [1, 1.05, 1], opacity: [0.25, 0.45, 0.25] }}
        transition={{ duration: 6, repeat: Infinity }}
        aria-hidden="true"
      />

      <motion.div
        initial={{ opacity: 0, y: 60 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, delay: 0.2 }}
        viewport={{ once: true }}
        className="z-30 max-w-3xl"
      >
        <h2 className="mb-6 text-4xl font-bold text-white drop-shadow-[0_0_20px_rgba(0,255,128,0.25)] md:text-6xl">
          {title}
        </h2>
        <p className="whitespace-pre-line text-lg leading-relaxed text-gray-200 md:text-xl">
          {text}
        </p>
        {showLaunchButton && (
          <div className="mt-8 flex justify-center">
            <a
              href="/hex_map.html"
              className="px-8 py-3 rounded-full border border-white/60 bg-white text-black font-semibold hover:bg-green-400/20 hover:text-white transition-all"
            >
              Launch Dashboard
            </a>
          </div>
        )}
      </motion.div>
    </section>
  );
}
