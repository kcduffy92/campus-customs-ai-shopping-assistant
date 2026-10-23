import { useRef, useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router";
import AuthLayout from "./AuthLayout.tsx";
import FormField, { useRevealErrors } from "../components/FormField.tsx";
import { useAuth } from "../auth/AuthContext.tsx";
import { ApiError } from "../api.ts";
import type { RegisterInput } from "../types.ts";

type Field = keyof RegisterInput;
type Errors = Partial<Record<Field, string>>;

const PASSWORD_MIN = 8;
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

/** Same rules the backend enforces, checked first so shoppers get instant feedback. */
function validate(v: RegisterInput): Errors {
  const e: Errors = {};
  if (!v.first_name.trim()) e.first_name = "Please enter your first name.";
  if (!v.last_name.trim()) e.last_name = "Please enter your last name.";
  if (!v.email.trim()) e.email = "Please enter your email.";
  else if (!EMAIL_RE.test(v.email.trim())) e.email = "Please enter a valid email address, like name@example.com.";
  if (!v.password) e.password = "Please create a password.";
  else if (v.password.length < PASSWORD_MIN) e.password = `Your password must be at least ${PASSWORD_MIN} characters.`;
  if (!v.confirm_password) e.confirm_password = "Please confirm your password.";
  else if (v.password && v.confirm_password !== v.password) e.confirm_password = "Passwords don't match.";
  return e;
}

export default function RegisterPage() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/account";

  const [values, setValues] = useState<RegisterInput>({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });
  const [errors, setErrors] = useState<Errors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [emailTaken, setEmailTaken] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const [failedAttempts, setFailedAttempts] = useState(0);
  // A duplicate email focuses the alert, which holds the "Sign in instead" link.
  useRevealErrors(formRef, failedAttempts, emailTaken);

  if (user && !submitting) return <Navigate to={from} replace />;

  const set = (field: Field) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setValues((v) => ({ ...v, [field]: e.target.value }));
    if (errors[field]) setErrors((er) => ({ ...er, [field]: undefined }));
  };

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const next = validate(values);
    setErrors(next);
    setFormError(null);
    setEmailTaken(false);
    if (Object.keys(next).length) {
      setFormError("Please fix the highlighted fields.");
      setFailedAttempts((n) => n + 1);
      return;
    }

    setSubmitting(true);
    try {
      await register({ ...values, first_name: values.first_name.trim(), last_name: values.last_name.trim(), email: values.email.trim() });
      navigate(from, { replace: true, state: { welcome: true } });
    } catch (err) {
      const apiErr = err instanceof ApiError ? err : null;
      setErrors((apiErr?.fields as Errors) ?? {});
      setFormError(apiErr?.message ?? "Something went wrong. Please try again.");
      setEmailTaken(apiErr?.status === 409);
      setSubmitting(false);
      setFailedAttempts((n) => n + 1);
    }
  }

  return (
    <AuthLayout title="Create an account" intro="It only takes a minute. We'll keep you signed in on this device.">
      <form ref={formRef} className="auth__form" onSubmit={onSubmit} noValidate>
        {formError && (
          <div className="form-alert" role="alert" tabIndex={-1}>
            {emailTaken ? (
              <>
                An account with this email already exists.{" "}
                <Link to="/account/login" state={location.state}>
                  Sign in instead
                </Link>
              </>
            ) : (
              formError
            )}
          </div>
        )}
        <div className="field-row">
          <FormField label="First name" name="first_name" autoComplete="given-name" value={values.first_name} onChange={set("first_name")} error={errors.first_name} maxLength={50} required />
          <FormField label="Last name" name="last_name" autoComplete="family-name" value={values.last_name} onChange={set("last_name")} error={errors.last_name} maxLength={50} required />
        </div>
        <FormField label="Email" type="email" name="email" autoComplete="email" inputMode="email" value={values.email} onChange={set("email")} error={errors.email} maxLength={254} required />
        <FormField
          label="Password"
          type="password"
          name="password"
          autoComplete="new-password"
          value={values.password}
          onChange={set("password")}
          error={errors.password}
          hint={`At least ${PASSWORD_MIN} characters.`}
          maxLength={128}
          required
        />
        <FormField
          label="Confirm password"
          type="password"
          name="confirm_password"
          autoComplete="new-password"
          value={values.confirm_password}
          onChange={set("confirm_password")}
          error={errors.confirm_password}
          maxLength={128}
          required
        />
        <button type="submit" className="button button--primary button--block" disabled={submitting}>
          {submitting ? "Creating your account…" : "Create account"}
        </button>
      </form>
      <p className="auth__switch">
        Already have an account?{" "}
        <Link to="/account/login" state={location.state}>
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
