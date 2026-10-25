// NOTIFICATION STEPS — the timeline of client notices of an alert (#275).
//
//   notificationSteps(alert, now)
//   // [{ key, title, detail, status }]  status: start | done | next | pending | call
//
// The backend sends the emails and returns them in `alert.notifications`
// ([{ attempt, channel, recipient, sent_at }]); this only turns that and the
// schedule below into the steps the panel draws. Without `notifications`
// (backend not ready yet) it returns [] and the panel shows nothing.

import { formatTime, parseDate } from "../composables/useFormat";

// Minutes after the alert. Same rule as #275: critical 5 and 20 min, then
// AquaGuard calls at 45; leve only one email at 60.
export const SCHEDULE = {
  CRITICAL: { emails: [5, 20], callAt: 45 },
  WARNING: { emails: [60], callAt: null },
};

const ORDINAL = ["1.er", "2.º", "3.er", "4.º"];

function at(alert, minutes) {
  const created = parseDate(alert.created_at);
  return created ? new Date(created.getTime() + minutes * 60000) : null;
}

function minutesUntil(date, now) {
  return Math.max(1, Math.ceil((date - now) / 60000));
}

export function notificationSteps(alert, now = new Date()) {
  if (!alert || !Array.isArray(alert.notifications)) return [];
  const schedule = SCHEDULE[alert.severity] ?? SCHEDULE.WARNING;
  const sent = new Map(alert.notifications.map((n) => [n.attempt, n]));
  // Someone took it (or it is closed): no more notices after that
  const stopped = alert.state !== "ACTIVE";

  const steps = [
    {
      key: "start",
      title: "Salta la alerta",
      detail: formatTime(alert.created_at),
      status: "start",
    },
  ];

  let nextMarked = false;
  schedule.emails.forEach((minutes, index) => {
    const attempt = index + 1;
    const name = `${ORDINAL[index]} email`;
    const notice = sent.get(attempt);
    if (notice) {
      steps.push({
        key: `email-${attempt}`,
        title: `${name} enviado`,
        detail: [formatTime(notice.sent_at), notice.recipient].filter(Boolean).join(" · "),
        status: "done",
      });
      return;
    }
    if (stopped) return;
    const when = at(alert, minutes);
    const isNext = !nextMarked;
    nextMarked = true;
    steps.push({
      key: `email-${attempt}`,
      title: isNext ? `${name} en ${minutesUntil(when, now)} min` : name,
      detail: formatTime(when),
      status: isNext ? "next" : "pending",
    });
  });

  if (stopped) {
    if (alert.acknowledged_at) {
      steps.push({
        key: "taken",
        title: `${alert.acknowledged_by_name || "Alguien del cliente"} se encarga`,
        detail: formatTime(alert.acknowledged_at),
        status: "done",
      });
    }
    return steps;
  }

  if (schedule.callAt !== null) {
    const callAt = at(alert, schedule.callAt);
    const due = callAt && callAt <= now;
    steps.push({
      key: "call",
      title: due ? "Nadie ha respondido: llama al cliente" : "Si nadie responde, llamar",
      detail: `${formatTime(callAt)} · AquaGuard`,
      status: due ? "call" : nextMarked ? "pending" : "next",
    });
  }

  return steps;
}

// One line for the table column "Avisos al cliente" (#275):
//   { main: 'Aún no', sub: 'en 2 min' }
//   { main: '1 aviso', sub: 'el 2.º en 9 min', tone: 'sent' }
//   { main: '2 avisos', sub: 'llamar', tone: 'call' }
// null without `notifications` (backend not ready): the table keeps "Nadie".
export function noticeSummary(alert, now = new Date()) {
  const steps = notificationSteps(alert, now);
  if (!steps.length) return null;
  const count = steps.filter((s) => s.status === "done").length;
  const main = count ? `${count} ${count === 1 ? "aviso" : "avisos"}` : "Aún no";
  const call = steps.find((s) => s.status === "call");
  if (call) return { main, sub: "llamar", tone: "call" };
  const next = steps.find((s) => s.status === "next");
  // "2.º email en 9 min" -> "el 2.º en 9 min"; "1.er email en 2 min" -> "en 2 min"
  const wait = next?.title.match(/(\S+) email en (.+)$/);
  let sub = "";
  if (wait) sub = count ? `el ${wait[1]} en ${wait[2]}` : `en ${wait[2]}`;
  else if (next) sub = next.title.toLowerCase();
  return { main, sub, tone: count ? "sent" : undefined };
}
