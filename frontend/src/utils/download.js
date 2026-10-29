// DOWNLOAD HELPER
// Saves a Blob as a file with the given name (CSV template, analytics export,
// "Descargar mis datos", documents).
// Two details make it work in every browser:
//   - the link is added to the page before the click: Firefox ignores clicks
//     on links that are not in the document;
//   - the blob URL is freed a moment after the click, not right away: Firefox
//     can cancel the download if the URL disappears while it starts.

export function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
