import Dither from "@/components/Dither";

export default function App() {
  return (
    <main className="relative isolate flex min-h-screen w-full flex-col items-center justify-center overflow-hidden bg-black px-6 py-12 text-white">
      {/* Animated background */}
      <div className="absolute inset-0 -z-10">
        <Dither
          className="pointer-events-none"
          waveColor={[0.5, 0.7, 0.5]}
          disableAnimation={false}
          enableMouseInteraction={false}
          mouseRadius={0.3}
          colorNum={7}
          waveAmplitude={0.15}
          waveFrequency={0.6}
          waveSpeed={0.05}
        />
      </div>

      <div className="text-center z-10">
      <h1 className="text-7xl font-extrabold tracking-tight"> GridCast </h1> 
      <p className="mt-4 text-xl text-white-200/80 max-w-xl"> Forecasting the energy of tomorrow, today. </p>
      </div>

      <div className="mt-10 flex flex-col space-y-4"> <button className="px-6 py-3 rounded-xl border border-white-400 text-white-300 hover:bg-white-500/10 transition"> Launch Dashboard </button> </div>
    </main>
  );
}
