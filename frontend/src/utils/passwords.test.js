import { describe, expect, it } from "vitest";
import { loginPasswordProblem, passwordProblem } from "./passwords";

describe("loginPasswordProblem", () => {
  it("asks for a password when nothing was typed", () => {
    expect(loginPasswordProblem("")).toBe("Introduce tu contraseña.");
    expect(loginPasswordProblem("   ")).toBe("Introduce tu contraseña.");
  });

  // No rule and no trimming at login: the backend answers 401
  it("lets through anything else, spaces included", () => {
    expect(loginPasswordProblem("corta")).toBeNull();
    expect(loginPasswordProblem(" dev-admin-only ")).toBeNull();
  });
});

describe("passwordProblem", () => {
  it("rejects spaces at either end, like the backend", () => {
    expect(passwordProblem(" una-contrasena-larga")).toMatch(/espacios/);
    expect(passwordProblem("una-contrasena-larga ")).toMatch(/espacios/);
  });

  it("checks the length limits", () => {
    expect(passwordProblem("a".repeat(11))).toMatch(/al menos 12/);
    expect(passwordProblem("a".repeat(129))).toMatch(/128/);
    expect(passwordProblem("una-contrasena-larga")).toBeNull();
  });

  it("rejects a password that contains the email", () => {
    expect(passwordProblem("xx-ana.medina-xx", "ana.medina@x.com")).toMatch(
      /email/,
    );
  });
});
