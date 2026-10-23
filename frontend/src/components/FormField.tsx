import { useEffect, useId, useState, type InputHTMLAttributes, type ReactNode, type RefObject } from "react";

/**
 * After a failed submit, bring the problem into view: focus the first invalid field (its message is right under it),
 * or, if no field is marked, the form's alert. Without this, on small phones the errors can sit above the visible
 * area after tapping the submit button at the bottom of the form.
 */
export function useRevealErrors(formRef: RefObject<HTMLFormElement | null>, attempt: number, preferAlert = false) {
  useEffect(() => {
    if (!attempt) return;
    const form = formRef.current;
    const field = form?.querySelector<HTMLElement>('[aria-invalid="true"]');
    const alert = form?.querySelector<HTMLElement>(".form-alert");
    (preferAlert ? alert ?? field : field ?? alert)?.focus();
  }, [attempt, formRef, preferAlert]);
}

interface FormFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "id"> {
  label: string;
  error?: string;
  hint?: ReactNode;
}

/** Labeled input with an inline error message. Password fields get a Show/Hide toggle. */
export default function FormField({ label, error, hint, type = "text", ...input }: FormFieldProps) {
  const id = useId();
  const [reveal, setReveal] = useState(false);
  const isPassword = type === "password";
  const describedBy = [error ? `${id}-error` : null, hint ? `${id}-hint` : null].filter(Boolean).join(" ") || undefined;

  return (
    <div className={`field${error ? " field--error" : ""}`}>
      <label htmlFor={id} className="field__label">
        {label}
      </label>
      <div className="field__control">
        <input
          id={id}
          className="input field__input"
          type={isPassword && reveal ? "text" : type}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          {...input}
        />
        {isPassword && (
          <button
            type="button"
            className="field__reveal"
            onClick={() => setReveal((r) => !r)}
            aria-label={reveal ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
            aria-pressed={reveal}
          >
            {reveal ? "Hide" : "Show"}
          </button>
        )}
      </div>
      {hint && !error && (
        <p id={`${id}-hint`} className="field__hint">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="field__error">
          {error}
        </p>
      )}
    </div>
  );
}
