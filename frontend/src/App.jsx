import Dither from "@/components/Dither";
import Navbar from "@/components/Navbar";

export default function App() {
  return (
    <main className="relative isolate flex min-h-screen w-full flex-col items-center justify-start overflow-hidden bg-black px-6 text-white">
      {/* Animated background */}
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

      {/* Navbar */}
      <Navbar />

      {/* Hero Section */}
      {/* Hero Section */}
        <section className="z-10 flex flex-col items-center justify-center text-center min-h-[70vh] pb-0 mb-0">
        <h1 className="text-6xl sm:text-7xl font-extrabold tracking-tight text-white drop-shadow-[0_0_15px_rgba(0,255,128,0.25)]">
          GridCast
        </h1>
        <p className="mt-4 text-lg sm:text-xl text-white/80 max-w-2xl">
          Forecasting the energy of tomorrow, today.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row gap-4">
          <button className="px-8 py-3 rounded-full border border-white-400/60 bg-white text-black font-semibold hover:bg-green-400/20 transition-all">
            Launch Dashboard
          </button>
          <button className="px-8 py-3 rounded-full border border-white/20 bg-white/5 text-white/80 font-medium hover:bg-white/10 transition-all">
            Learn More
          </button>
        </div>
      </section>

      {/* Features Section */}
      <section className="z-10 grid grid-cols-1 sm:grid-cols-3 gap-8 max-w-6xl">
        <div className="rounded-2xl bg-white/5 border border-white/10 p-6 backdrop-blur-md text-center hover:bg-white/10 transition">
          <h3 className="text-xl font-semibold text-white-300 mb-2">Real-Time Insights</h3>
          <p className="text-white/70">
            Live data visualizations of regional and national energy grids to stay ahead of market shifts.
          </p>
        </div>
        <div className="rounded-2xl bg-white/5 border border-white/10 p-6 backdrop-blur-md text-center hover:bg-white/10 transition">
          <h3 className="text-xl font-semibold text-white-300 mb-2">AI Forecasting</h3>
          <p className="text-white/70">
            Powered by advanced ARIMA + neural hybrid models for accurate energy demand predictions.
          </p>
        </div>
        <div className="rounded-2xl bg-white/5 border border-white/10 p-6 backdrop-blur-md text-center hover:bg-white/10 transition">
          <h3 className="text-xl font-semibold text-white-300 mb-2">Sustainability Index</h3>
          <p className="text-white/70">
            Balance profitability and sustainability with our datacenter and ESG scoring models.
          </p>
        </div>
      </section>


    </main>
  );
}
