import React, { useState } from "react";

export default function SearchForm({ onSearch, loading }) {
  const [q, setQ] = useState("");

  function submit(e) {
    e.preventDefault();
    if (!q.trim()) return alert("Please enter a query");
    onSearch(q.trim());
  }

  return (
    <form 
      onSubmit={submit}
      className="flex items-center gap-3 bg-white/5 backdrop-blur-lg 
                 p-4 rounded-2xl border border-white/10"
    >
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Ask AI something... (e.g. '24h cafe in Depok')"
        className="flex-1 px-4 py-3 bg-transparent border border-white/10 
                   rounded-xl text-gray-200 placeholder-gray-500 
                   focus:border-blue-500 outline-none transition"
      />

      <button
        disabled={loading}
        className={`px-5 py-3 rounded-xl font-semibold text-white transition
          ${loading 
            ? "bg-gray-600 cursor-not-allowed" 
            : "bg-blue-600 hover:bg-blue-700"
          }`}
      >
        {loading ? "Searching..." : "Search"}
      </button>
    </form>
  );
}
