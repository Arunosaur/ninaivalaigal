// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

export default function Home() {
  return (
    <main className="bg-black text-gray-100 font-sans">
      {/* HERO SECTION */}
      <section className="relative bg-gradient-to-b from-indigo-950 via-gray-900 to-black text-gray-100 py-28 px-6 overflow-hidden">
        {/* Subtle background glow */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-indigo-600/20 via-transparent to-transparent" />

        <div className="relative max-w-5xl mx-auto text-center space-y-8">
          <h1 className="text-5xl md:text-6xl font-extrabold leading-tight tracking-tight">
            Capture knowledge once.<br />
            Recall it forever.
          </h1>
          <p className="text-lg md:text-xl text-gray-400 max-w-3xl mx-auto leading-relaxed">
            Transform your organization's collective intelligence into a living memory graph -- align teams, accelerate insights, and never lose context again.
          </p>

          <div className="flex justify-center gap-4 pt-6">
            <button className="px-8 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition">
              Start Free Trial
            </button>
            <button className="px-8 py-3 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-800">
              Explore Live Demo
            </button>
          </div>
        </div>
      </section>

      {/* FEATURE GRID */}
      <section className="bg-gray-950 py-24 px-6 text-gray-100 border-t border-gray-800">
        <div className="max-w-6xl mx-auto text-center space-y-12">
          <h2 className="text-3xl font-semibold">Why Ninaivalaigal?</h2>
          <div className="grid md:grid-cols-3 gap-12">
            <Feature
              icon="🧠"
              title="Exponential Memory"
              desc="Every captured insight becomes a node in a connected graph that grows smarter over time."
            />
            <Feature
              icon="⚡"
              title="AI Insights"
              desc="Semantic reasoning surfaces patterns, correlations, and context automatically."
            />
            <Feature
              icon="🤝"
              title="Team Collaboration"
              desc="Share context seamlessly with fine-grained access and audit control."
            />
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="bg-gray-900 py-24 px-6 border-t border-gray-800">
        <div className="max-w-6xl mx-auto text-center space-y-12">
          <h2 className="text-3xl font-semibold">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-12">
            <Step
              number="1"
              title="Capture"
              desc="Pull information from chats, documents, and meetings into your memory graph."
            />
            <Step
              number="2"
              title="Connect"
              desc="AI links related ideas, detects themes, and forms semantic relationships."
            />
            <Step
              number="3"
              title="Recall"
              desc="Retrieve instant insights with context-aware, intelligent search."
            />
          </div>
        </div>
      </section>

      {/* CTA SECTION */}
      <section className="bg-indigo-700 text-white text-center py-20">
        <h2 className="text-4xl font-bold mb-6">Your collective intelligence, amplified.</h2>
        <button className="px-8 py-3 bg-white text-indigo-700 font-semibold rounded-lg hover:bg-gray-100">
          Get Started Free
        </button>
      </section>

      {/* FOOTER */}
      <footer className="bg-black py-12 text-center text-gray-500 text-sm border-t border-gray-800">
        <p>© 2025 Medhasys LLC · Ninaivalaigal -- Exponential Memory System</p>
      </footer>
    </main>
  );
}

function Feature({
  icon,
  title,
  desc,
}: {
  icon: string;
  title: string;
  desc: string;
}) {
  return (
    <div className="space-y-4">
      <div className="text-4xl">{icon}</div>
      <h3 className="text-xl font-semibold text-gray-100">{title}</h3>
      <p className="text-gray-400 text-base leading-relaxed">{desc}</p>
    </div>
  );
}

function Step({
  number,
  title,
  desc,
}: {
  number: string;
  title: string;
  desc: string;
}) {
  return (
    <div className="space-y-4">
      <div className="text-indigo-500 font-bold text-3xl">{number}</div>
      <h3 className="text-xl font-semibold text-gray-100">{title}</h3>
      <p className="text-gray-400 text-base leading-relaxed">{desc}</p>
    </div>
  );
}
