import { describe, expect, it } from "vitest";
import { nextTick, reactive } from "vue";
import { useFieldErrors } from "./useFieldErrors";

describe("useFieldErrors", () => {
  it("checks the rules and says if all pass", () => {
    const { errors, check, firstError } = useFieldErrors(["name", "email"]);

    expect(check({ name: () => null, email: () => "Escribe el email." })).toBe(
      false,
    );
    expect(errors).toEqual({ name: "", email: "Escribe el email." });
    expect(firstError()).toBe("email");
    expect(check({ email: () => null })).toBe(true);
  });

  it("marks a wrong field the same way in every form", () => {
    const { errors, inputClass, fieldAttrs, errorId } = useFieldErrors(
      ["name"],
      { size: "lg" },
    );

    expect(inputClass("name").join(" ")).toContain("border-slate-300");
    expect(fieldAttrs("name", "hint")).toEqual({
      "aria-invalid": undefined,
      "aria-describedby": "hint",
    });

    errors.name = "El nombre no puede estar vacío.";
    expect(inputClass("name", "pr-20").join(" ")).toContain(
      "px-4 py-3 pr-20 border-danger bg-danger-light/40",
    );
    expect(fieldAttrs("name", "hint")).toEqual({
      "aria-invalid": "true",
      "aria-describedby": `hint ${errorId("name")}`,
    });
  });

  it("clears an error as soon as the field is edited", async () => {
    const form = reactive({ name: "" });
    const state = useFieldErrors(["name"]);
    state.clearOnEdit({ name: () => form.name });

    state.errors.name = "El nombre no puede estar vacío.";
    form.name = "Ana";
    await nextTick();
    expect(state.errors.name).toBe("");
  });

  describe("applyApiError", () => {
    it("puts a domain code under its field, with the backend message", () => {
      const { errors, applyApiError } = useFieldErrors(["phone"]);
      const error = {
        code: "INVALID_PHONE",
        message: "Escribe un teléfono español.",
      };

      expect(applyApiError(error, { codes: { INVALID_PHONE: "phone" } })).toBe(
        true,
      );
      expect(errors.phone).toBe("Escribe un teléfono español.");
    });

    it("can use our own text for a code", () => {
      const { errors, applyApiError } = useFieldErrors(["name"]);
      const codes = {
        ORGANIZATION_NAME_TAKEN: {
          field: "name",
          message: "Ya hay un cliente con este nombre.",
        },
      };

      applyApiError(
        { code: "ORGANIZATION_NAME_TAKEN", message: "x" },
        { codes },
      );
      expect(errors.name).toBe("Ya hay un cliente con este nombre.");
    });

    it("uses details[0].field when the code is not mapped", () => {
      const { errors, applyApiError } = useFieldErrors([
        "name",
        "organization_name",
      ]);
      const error = {
        code: "INVALID_NAME",
        message: "El nombre solo puede tener letras…",
        details: [{ field: "organization_name" }],
      };

      expect(applyApiError(error)).toBe(true);
      expect(errors.organization_name).toBe(
        "El nombre solo puede tener letras…",
      );
      expect(errors.name).toBe("");
    });

    it("gives a Spanish text to the English messages of VALIDATION_ERROR", () => {
      const { errors, applyApiError } = useFieldErrors(["address"]);
      const error = {
        code: "VALIDATION_ERROR",
        details: [
          {
            field: "billing_address",
            message: "String should have at most 200 characters",
          },
        ],
      };

      applyApiError(error, {
        aliases: { billing_address: "address" },
        messages: { address: "Escribe la dirección fiscal." },
      });
      expect(errors.address).toBe("Escribe la dirección fiscal.");
    });

    it("returns false for an error of no field", () => {
      const { applyApiError } = useFieldErrors(["name"]);
      expect(
        applyApiError({ code: "NETWORK_ERROR", message: "Network Error" }),
      ).toBe(false);
    });
  });
});
