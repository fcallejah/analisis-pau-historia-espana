document.querySelectorAll(".reading-video-player").forEach((player) => {
  const iframe = document.createElement("iframe");
  iframe.src = `https://www.youtube-nocookie.com/embed/${player.dataset.videoId}`;
  iframe.title = "Sociedad Económica de Amigos del País de Málaga";
  iframe.allow = "accelerometer; encrypted-media; gyroscope; picture-in-picture";
  iframe.allowFullscreen = true;
  iframe.referrerPolicy = "strict-origin-when-cross-origin";
  player.replaceChildren(iframe);
});
