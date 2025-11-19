import React, { useState } from "react";
import SearchForm from "./SearchForm";
import MapEmbed from "./MapEmbed";

export default function App() {
  const [places, setPlaces] = useState([]);
  const [loading, setLoading] = useState(false);

  async function onSearch(query) {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, limit: 5 }),
      });
      const j = await res.json();
      setPlaces(j.results || []);
    } catch (err) {
      alert("Request failed: " + err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0F0F10] text-gray-100 flex flex-col">

      {/* Header */}
      <header className="py-6 border-b border-white/10 backdrop-blur-lg">
        <h1 className="text-center text-3xl font-semibold tracking-wide">
          🔍 AI Places Finder
        </h1>
      </header>

      <main className="flex-grow max-w-3xl w-full mx-auto py-8 px-4 flex flex-col gap-8">

        {/* Input Section */}
        <SearchForm onSearch={onSearch} loading={loading} />

        {/* Results */}
        <div className="flex flex-col gap-6">
          {places.length === 0 && !loading && (
            <p className="text-center text-gray-400 mt-10">
              Start by asking:  
              <span className="text-blue-400"> “Find coffee shops near me”</span>
            </p>
          )}

          {places.map((p, i) => (
            <div
              key={i}
              className="bg-white/5 border border-white/10 p-5 rounded-2xl shadow-xl backdrop-blur-xl transition hover:scale-[1.01]"
            >
              <h3 className="text-xl font-semibold text-white">{p.name}</h3>
              <p className="text-sm text-gray-400 mb-3">{p.address}</p>

              <div className="w-full h-72 rounded-xl overflow-hidden border border-white/10 mb-4">
                <MapEmbed src={p.embed_src} name={p.name} />
              </div>

              <a
                href={p.directions_url}
                target="_blank"
                rel="noreferrer"
                className="inline-block px-4 py-2 bg-blue-600 hover:bg-blue-700 
                           text-white rounded-lg font-medium transition"
              >
                📍 Open Directions
              </a>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
