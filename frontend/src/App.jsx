import Dither from "@/components/Dither";

export default function App() {
  return (
    <main className="relative flex flex-col items-center justify-center min-h-screen overflow-hidden bg-black text-white">
      {/* Dither Background */}
      <div cstyle={{ width: '100%', height: '600px', position: 'relative' }}>
        <Dither
          waveColor={[0.5, 0.7, 0.5]}     // RGB greyish tone
          disableAnimation={false}         // keep it moving
          enableMouseInteraction={false}    // reactive to mouse
          mouseRadius={0.5}
          colorNum={6.7}
          waveAmplitude={0.1}
          waveFrequency={0.1}
          waveSpeed={0.005}
        />
      </div>

      {/* Foreground content */}
      <div className="text-center z-10">
      <h1 className="text-7xl font-extrabold tracking-tight"> GridCast </h1> 
      <p className="mt-4 text-xl text-green-200/80 max-w-xl"> Forecasting the energy of tomorrow, today. </p>
      </div>

      <div className="mt-10 flex flex-col space-y-4"> <button className="px-6 py-3 rounded-xl border border-green-400 text-green-300 hover:bg-green-500/10 transition"> Launch Dashboard </button> </div>
    </main>
  );
}
