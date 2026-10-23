import { useRef, useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router";
import AuthLayout from "./AuthLayout.tsx";
import FormField, { useRevealErrors } from "../components/FormField.tsx";
import { useAuth } from "../auth/AuthContext.tsx";
import { ApiError } from "../api.ts";

type Errors = Partial<Record<"email" | "password", string>>;

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/account";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const [failedAttempts, setFailedAttempts] = useState(0);
  useRevealErrors(formRef, failedAttempts);

  if (user && !submitting) return <Navigate to={from} replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const next: Errors = {};
    if (!email.trim()) next.email = "Please enter your email.";
    if (!password) next.password = "Please enter your password.";
    setErrors(next);
    setFormError(null);
    if (Object.keys(next).length) {
      setFailedAttempts((n) => n + 1);
      return;
    }

    setSubmitting(true);
    try {
      await login({ email: email.trim(), password });
      navigate(from, { replace: true });
    } catch (err) {
      const apiErr = err instanceof ApiError ? err : null;
      setErrors(apiErr?.fields ?? {});
      setFormError(apiErr?.message ?? "Something went wrong. Please try again.");
      setPassword("");
      setSubmitting(false);
      setFailedAttempts((n) => n + 1);
    }
  }

  return (
    <AuthLayout title="Sign in" intro="Welcome back! Sign in with the email and password you used to create your account.">
      <form ref={formRef} className="auth__form" onSubmit={onSubmit} noValidate>
        {formError && (
          <div className="form-alert" role="alert" tabIndex={-1}>
            {formError}
          </div>
        )}
        <FormField
          label="Email"
          type="email"
          name="email"
          autoComplete="email"
          inputMode="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.email}
          maxLength={254}
          required
        />
        <FormField
          label="Password"
          type="password"
          name="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.password}
          maxLength={128}
          required
        />
        <button type="submit" className="button button--primary button--block" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className="auth__switch">
        New to Campus Customs?{" "}
        <Link to="/account/register" state={location.state}>
          Create an account
        </Link>
      </p>
    </AuthLayout>
  );
}
