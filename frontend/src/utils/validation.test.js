import { describe, expect, it } from "vitest";
import {
  apiErrorField,
  cleanText,
  compactCode,
  emailProblem,
  ibanProblem,
  normalizeEmail,
  normalizePhone,
  ORGANIZATION_NAME_MESSAGE,
  organizationNameProblem,
  personNameProblem,
  phoneProblem,
  postalCodeProblem,
  taxIdProblem,
} from "./validation";

// Same cases as backend/tests/test_fields.py
describe("phone", () => {
  it.each([
    "612345678",
    "612 345 678",
    "612.34.56.78",
    "612-345-678",
    "+34 612 345 678",
    "+34612345678",
    "0034 612 345 678",
    "(+34) 612 34 56 78",
  ])("accepts %s and stores it as +34 612 345 678", (value) => {
    expect(phoneProblem(value)).toBeNull();
    expect(normalizePhone(value)).toBe("+34 612 345 678");
  });

  it("accepts a landline", () => {
    expect(normalizePhone("93 123 45 67")).toBe("+34 931 234 567");
  });

  it("is required", () => {
    expect(phoneProblem("")).toBe("El teléfono es obligatorio.");
    expect(phoneProblem("   ")).toBe("El teléfono es obligatorio.");
  });

  it.each([
    "12345678",
    "512345678",
    "6123456789",
    "+33 612 345 678",
    "612 345 67a",
  ])("rejects %s", (value) => {
    expect(phoneProblem(value)).toMatch(/teléfono español/);
  });
});

describe("organizationNameProblem", () => {
  it.each([
    "Hotel Mar",
    "Hotel Gòtic",
    "Comunidad Mallorca 401",
    "Aigües Zona Franca",
    "Ca n'Oller",
    "Hotel Mar, S.L.",
    "Mar & Sol (Gràcia)",
  ])("accepts %s", (value) => {
    expect(organizationNameProblem(value)).toBeNull();
  });

  it.each(["Mar!", "A/B", "Hotel@Mar", "Hotel #1", "<script>", "...", "&"])(
    "rejects %s",
    (value) => {
      expect(organizationNameProblem(value)).toBe(ORGANIZATION_NAME_MESSAGE);
    },
  );

  it("rejects an empty name and a long one", () => {
    expect(organizationNameProblem("   ")).toMatch(/vacío/);
    expect(organizationNameProblem("x".repeat(121))).toMatch(/120/);
  });
});

describe("personNameProblem", () => {
  it.each(["Ana Medina", "Laura P.", "María O'Neill-Pérez"])(
    "accepts %s",
    (value) => {
      expect(personNameProblem(value)).toBeNull();
    },
  );

  it.each(["Ana 2", "ana@mar.dev", "<script>", "..."])(
    "rejects %s",
    (value) => {
      expect(personNameProblem(value)).toMatch(/solo puede tener letras/);
    },
  );

  it("rejects an empty name", () => {
    expect(personNameProblem("  ")).toMatch(/vacío/);
  });
});

describe("email", () => {
  it("is required unless said otherwise", () => {
    expect(emailProblem("")).toBe("Escribe el email.");
    expect(emailProblem("", { required: false })).toBeNull();
  });

  it("checks the shape and the length", () => {
    expect(emailProblem("ana@mar")).toMatch(/válido/);
    expect(emailProblem(`${"a".repeat(320)}@mar.dev`)).toMatch(/válido/);
    expect(emailProblem(" ana@mar.dev ")).toBeNull();
  });

  it("is stored in lowercase", () => {
    expect(normalizeEmail(" Ana@Mar.DEV ")).toBe("ana@mar.dev");
  });
});

describe("tax id, postal code and IBAN", () => {
  it("compacts the tax id", () => {
    expect(compactCode(" x-1234567.l ")).toBe("X1234567L");
    expect(taxIdProblem("b-1234 5678")).toBeNull();
    expect(taxIdProblem("1")).toMatch(/NIF o CIF válido/);
    expect(taxIdProblem("", { required: false })).toBeNull();
  });

  it("wants five digits in the postal code", () => {
    expect(postalCodeProblem("08002")).toBeNull();
    expect(postalCodeProblem("8002")).toMatch(/5 cifras/);
  });

  it("checks the IBAN shape and check digits", () => {
    expect(ibanProblem("ES91 2100 0418 4502 0005 1332")).toBeNull();
    expect(ibanProblem("ES92 2100 0418 4502 0005 1332")).toMatch(/dígitos/);
    expect(ibanProblem("DE89 3704 0044 0532 0130 00")).toMatch(/español/);
  });
});

describe("helpers", () => {
  it("cleans the spaces of a text", () => {
    expect(cleanText("  Carrer   de la Lluna 1 ")).toBe("Carrer de la Lluna 1");
    expect(cleanText("Hotel Gòtic")).toBe("Hotel Gòtic");
  });

  it("reads the field of an API error", () => {
    expect(apiErrorField({ details: [{ field: "name" }] })).toBe("name");
    expect(apiErrorField({ details: null })).toBeNull();
  });
});
