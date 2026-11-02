// useFieldErrors — one way to keep, show and focus the errors of a form.
//
// Every form of the app uses it, so a wrong field looks and behaves the same
// everywhere: red border and light red background, the message under the
// field (<FieldError>), aria-invalid + aria-describedby, the focus on the
// first wrong field, and the error gone as soon as the field is edited.
// The rules themselves are in utils/validation.js and utils/passwords.js.
//
//   const { errors, inputClass, fieldAttrs, errorId, setRef, check,
//           focusFirstError, applyApiError } = useFieldErrors(["name", "email"]);
//
//   check({ name: () => personNameProblem(form.name), email: ... })
//   <input :ref="setRef('name')" :class="inputClass('name')" v-bind="fieldAttrs('name')" />
//   <FieldError :id="errorId('name')" :message="errors.name" />

import { getCurrentInstance, nextTick, reactive, useId, watch } from "vue";

// Same input everywhere; `size` only changes the padding: "lg" on the
// public pages and the subscribe page, "md" inside the panels
export const INPUT_CLASS =
  "w-full rounded-lg border bg-white text-base focus:outline-none focus:ring-2 focus:ring-aqua-600";
export const INPUT_SIZE = { md: "px-3 py-2", lg: "px-4 py-3" };
export const INPUT_ERROR_CLASS = "border-danger bg-danger-light/40";
export const INPUT_OK_CLASS = "border-slate-300";

export function useFieldErrors(fields, { size = "md" } = {}) {
  const errors = reactive(
    Object.fromEntries(fields.map((field) => [field, ""])),
  );
  const inputs = {};
  // Unique per component, so two forms on a page never share ids. Outside a
  // component (unit tests) there is only one form
  const uid = getCurrentInstance() ? useId() : "form";

  function errorId(field) {
    return `${uid}-${field}-error`;
  }

  // Function ref: <input :ref="setRef('name')">
  function setRef(field) {
    return (el) => {
      inputs[field] = el;
    };
  }

  // `extra`: classes of this input only (pr-20 for the show password button)
  function inputClass(field, extra = "") {
    return [
      INPUT_CLASS,
      INPUT_SIZE[size],
      extra,
      errors[field] ? INPUT_ERROR_CLASS : INPUT_OK_CLASS,
    ];
  }

  // `hintId`: a hint under the field that is always read with it
  function fieldAttrs(field, hintId = null) {
    const describedBy = [hintId, errors[field] ? errorId(field) : null]
      .filter(Boolean)
      .join(" ");
    return {
      "aria-invalid": errors[field] ? "true" : undefined,
      "aria-describedby": describedBy || undefined,
    };
  }

  function clear() {
    for (const field of fields) errors[field] = "";
  }

  // rules: { field: () => message | null }. Returns true when all pass
  function check(rules) {
    for (const [field, rule] of Object.entries(rules)) {
      errors[field] = rule() ?? "";
    }
    return Object.keys(rules).every((field) => !errors[field]);
  }

  function firstError() {
    return fields.find((field) => errors[field]) ?? null;
  }

  // Focus the first wrong field, in the order of `fields` (screen order)
  async function focusFirstError() {
    await nextTick();
    const field = firstError();
    if (field) inputs[field]?.focus?.();
    return field;
  }

  // Clears a field's error as soon as the user edits it.
  // getters: { field: () => value }
  function clearOnEdit(getters) {
    for (const [field, getter] of Object.entries(getters)) {
      watch(getter, () => {
        errors[field] = "";
      });
    }
  }

  // Puts an API error (already normalized by the adapter) under its field.
  // Returns true when it belonged to a field, false when it is general.
  //   codes:    { CODE: "field" }          domain codes of one field, or
  //             { CODE: { field, message } } with our own text
  //   messages: { field: "text" }          our text for a VALIDATION_ERROR
  //   aliases:  { api_field: "field" }     API name → field on screen
  // The backend message is used as is: it is in Spanish and says what is
  // wrong (backend/app/shared/fields.py writes the same as validation.js).
  function applyApiError(
    error,
    { codes = {}, messages = {}, aliases = {} } = {},
  ) {
    const screenField = (apiField) => aliases[apiField] ?? apiField;
    const details = Array.isArray(error?.details) ? error.details : [];

    // Generic 422 of Pydantic: one detail per field, messages in English
    if (error?.code === "VALIDATION_ERROR") {
      let matched = false;
      for (const detail of details) {
        const field = screenField(detail?.field);
        if (field in errors) {
          errors[field] = messages[field] ?? "Revisa este campo.";
          matched = true;
        }
      }
      return matched;
    }

    // Domain error: the code, or details[0].field, says which field
    const byCode = codes[error?.code];
    const field =
      (typeof byCode === "string" ? byCode : byCode?.field) ??
      screenField(details[0]?.field);
    if (field in errors) {
      errors[field] = byCode?.message ?? error.message;
      return true;
    }
    return false;
  }

  return {
    errors,
    inputs,
    errorId,
    setRef,
    inputClass,
    fieldAttrs,
    clear,
    check,
    firstError,
    focusFirstError,
    clearOnEdit,
    applyApiError,
  };
}
