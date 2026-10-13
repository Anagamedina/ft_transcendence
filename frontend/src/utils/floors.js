// FLOOR HELPERS
// Floor numbering agreed in B2/B3:
//   0 is the ground floor, positive numbers are floors above ground,
//   negative numbers are basements.
// `floors` counts the ground floor, so a building goes from
// -basements to floors - 1 (same rule the backend validates).

// 'Planta baja', 'Planta 3', 'Sótano 1'
export function floorLabel(floor) {
  if (floor === 0) return 'Planta baja'
  if (floor > 0) return `Planta ${floor}`
  return `Sótano ${-floor}`
}

// Every floor of the building from top to bottom, ready to draw it.
// Example: floors 3, basements 1 -> [2, 1, 0, -1]
export function floorRange(floors, basements) {
  const top = Math.max(Number(floors) || 1, 1) - 1
  const bottom = -Math.max(Number(basements) || 0, 0)
  const list = []
  for (let floor = top; floor >= bottom; floor--) list.push(floor)
  return list
}
