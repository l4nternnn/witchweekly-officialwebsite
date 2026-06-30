const escapeHtml = (value) =>
  String(value || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')

const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

export const highlightMatches = (value, query) => {
  const escaped = escapeHtml(value)
  const terms = String(query || '')
    .trim()
    .split(/\s+/)
    .filter(Boolean)

  if (!terms.length) {
    return escaped
  }

  const pattern = new RegExp(`(${terms.map(escapeRegExp).join('|')})`, 'gi')
  return escaped.replace(pattern, '<mark class="search-hit">$1</mark>')
}
