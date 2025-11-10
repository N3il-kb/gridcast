export default function Navbar() {
    return (
      <header className="fixed top-6 left-1/2 z-20 -translate-x-1/2">
        <nav className="flex items-center gap-8 rounded-full border border-white/10 bg-black/40 px-8 py-3 shadow-[0_0_20px_rgba(0,255,128,0.15)] backdrop-blur-md">
          {/* Logo + Title */}
          <div className="flex items-center gap-2">
            {/* <div className="h-6 w-6 rounded-full bg-gradient-to-br from-green-400 to-emerald-600" /> */}
            <span className="text-lg font-semibold tracking-tight text-white">
              GridCast
            </span>
          </div>
  
          {/* Nav links */}
          <ul className="flex items-center gap-6 text-sm text-white/70">
            <li>
              <a
                href="#"
                className="transition hover:text-white hover:drop-shadow-[0_0_6px_rgba(0,255,128,0.6)]"
              >
                Dashboard
              </a>
            </li>
            <li>
              <a
                href="#"
                className="transition hover:text-white hover:drop-shadow-[0_0_6px_rgba(0,255,128,0.6)]"
              >
                About
              </a>
            </li>
            <li>
              <a
                href="#"
                className="transition hover:text-white hover:drop-shadow-[0_0_6px_rgba(0,255,128,0.6)]"
              >
                Contact
              </a>
            </li>
          </ul>
        </nav>
      </header>
    );
  }
  