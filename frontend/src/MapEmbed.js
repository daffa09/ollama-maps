import React from "react";

export default function MapEmbed({ src, name }) {
  return (
    <iframe
      title={name}
      src={src}
      className="w-full h-full border-0 rounded-xl"
      allowFullScreen
      loading="lazy"
    />
  );
}
