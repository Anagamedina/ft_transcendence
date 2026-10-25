import { describe, expect, it } from "vitest";
import { noticeSummary, notificationSteps } from "./notificationSteps";

const CREATED = "2026-10-25T10:00:00Z";
const minutesLater = (m) => new Date(Date.parse(CREATED) + m * 60000);

function critical(extra = {}) {
  return {
    severity: "CRITICAL",
    state: "ACTIVE",
    created_at: CREATED,
    notifications: [],
    ...extra,
  };
}

const view = (steps) => steps.map((s) => [s.title, s.status]);

describe("notificationSteps", () => {
  it("shows nothing while the backend does not send notifications", () => {
    expect(notificationSteps({ severity: "CRITICAL", state: "ACTIVE" })).toEqual([]);
  });

  it("marks what was sent and highlights the next one", () => {
    const alert = critical({
      notifications: [
        { attempt: 1, channel: "EMAIL", recipient: "a@b.es", sent_at: "2026-10-25T10:05:00Z" },
      ],
    });
    expect(view(notificationSteps(alert, minutesLater(11)))).toEqual([
      ["Salta la alerta", "start"],
      ["1.er email enviado", "done"],
      ["2.º email en 9 min", "next"],
      ["Si nadie responde, llamar", "pending"],
    ]);
  });

  it("asks AquaGuard to call when nobody answered in time", () => {
    const alert = critical({
      notifications: [
        { attempt: 1, sent_at: "2026-10-25T10:05:00Z" },
        { attempt: 2, sent_at: "2026-10-25T10:20:00Z" },
      ],
    });
    const steps = notificationSteps(alert, minutesLater(50));
    expect(steps.at(-1)).toMatchObject({
      title: "Nadie ha respondido: llama al cliente",
      status: "call",
    });
  });

  it("stops when someone takes it", () => {
    const alert = critical({
      state: "ACKNOWLEDGED",
      acknowledged_at: "2026-10-25T10:12:00Z",
      acknowledged_by_name: "Jordi Vidal",
      notifications: [{ attempt: 1, sent_at: "2026-10-25T10:05:00Z" }],
    });
    expect(view(notificationSteps(alert, minutesLater(30)))).toEqual([
      ["Salta la alerta", "start"],
      ["1.er email enviado", "done"],
      ["Jordi Vidal se encarga", "done"],
    ]);
  });

  it("a leve gets a single email and no call", () => {
    const alert = { ...critical(), severity: "WARNING" };
    expect(view(notificationSteps(alert, minutesLater(20)))).toEqual([
      ["Salta la alerta", "start"],
      ["1.er email en 40 min", "next"],
    ]);
  });
});

describe("noticeSummary", () => {
  it("is null while the backend does not send notifications", () => {
    expect(noticeSummary({ severity: "CRITICAL", state: "ACTIVE" })).toBeNull();
  });

  it("says when the first notice goes out", () => {
    expect(noticeSummary(critical(), minutesLater(3))).toEqual({
      main: "Aún no",
      sub: "en 2 min",
      tone: undefined,
    });
  });

  it("counts the notices and says when the next one goes out", () => {
    const alert = critical({ notifications: [{ attempt: 1, sent_at: "2026-10-25T10:05:00Z" }] });
    expect(noticeSummary(alert, minutesLater(11))).toEqual({
      main: "1 aviso",
      sub: "el 2.º en 9 min",
      tone: "sent",
    });
  });

  it("asks to call when nobody answered", () => {
    const alert = critical({
      notifications: [
        { attempt: 1, sent_at: "2026-10-25T10:05:00Z" },
        { attempt: 2, sent_at: "2026-10-25T10:20:00Z" },
      ],
    });
    expect(noticeSummary(alert, minutesLater(50))).toEqual({
      main: "2 avisos",
      sub: "llamar",
      tone: "call",
    });
  });
});
