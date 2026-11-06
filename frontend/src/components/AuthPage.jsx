import React, { useState } from 'react';
import { ArrowRight, Eye, EyeOff, LockKeyhole, Mail, Shirt, Sparkles, UserRound } from 'lucide-react';
import './AuthPage.css';

const API_BASE = 'http://localhost:8000';

export default function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const isRegistering = mode === 'register';

  const switchMode = nextMode => {
    setMode(nextMode);
    setError('');
    setPassword('');
    setConfirmPassword('');
  };

  const handleSubmit = async event => {
    event.preventDefault();
    setError('');
    if (isRegistering && password !== confirmPassword) {
      setError('Your passwords do not match.');
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/api/auth/${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          password,
          ...(isRegistering ? { name: name.trim() } : {})
        })
      });
      const data = await response.json();
      if (!response.ok || data.status !== 'success') {
        throw new Error(data.detail || 'We could not complete your request. Please try again.');
      }
      onAuthenticated(data.user);
    } catch (requestError) {
      setError(requestError instanceof TypeError
        ? 'Could not connect to the wardrobe server. Make sure the backend is running and try again.'
        : requestError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-showcase" aria-label="Smart Wardrobe introduction">
        <div className="auth-showcase-overlay" />
        <div className="auth-brand">
          <span className="auth-brand-mark"><Shirt size={21} strokeWidth={2.2} /></span>
          <span>Smart Wardrobe</span>
        </div>
        <div className="auth-showcase-copy">
          <span className="auth-eyebrow"><Sparkles size={14} /> YOUR STYLE, MADE SIMPLE</span>
          <h1>Make getting dressed the best part of your day.</h1>
          <p>Meet your personal AI stylist. Bring your wardrobe together and find a look that feels like you.</p>
          <div className="auth-showcase-note">
            <span className="auth-note-icon"><Sparkles size={16} /></span>
            <span><strong>A little more you, every day.</strong><small>Thoughtful outfit ideas from the clothes you own.</small></span>
          </div>
        </div>
        <span className="auth-showcase-footer">A smarter way to wear your wardrobe</span>
      </section>

      <section className="auth-form-side">
        <div className="auth-form-wrap">
          <div className="auth-mobile-brand">
            <span className="auth-brand-mark"><Shirt size={20} /></span>
            <span>Smart Wardrobe</span>
          </div>
          <div className="auth-form-heading">
            <span className="auth-welcome-icon"><Sparkles size={18} /></span>
            <p className="auth-kicker">{isRegistering ? 'YOUR STYLE JOURNEY STARTS HERE' : 'WELCOME BACK'}</p>
            <h2>{isRegistering ? 'Create your account' : 'Sign in to your wardrobe'}</h2>
            <p className="auth-subtitle">
              {isRegistering
                ? 'A few details and your personal stylist is ready.'
                : 'Your next great outfit is just around the corner.'}
            </p>
          </div>

          <div className="auth-mode-switch" role="tablist" aria-label="Account access">
            <button type="button" role="tab" aria-selected={!isRegistering} className={!isRegistering ? 'is-selected' : ''} onClick={() => switchMode('login')}>
              Sign in
            </button>
            <button type="button" role="tab" aria-selected={isRegistering} className={isRegistering ? 'is-selected' : ''} onClick={() => switchMode('register')}>
              Create account
            </button>
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>
            {isRegistering && (
              <label className="auth-field">
                <span>Your name</span>
                <span className="auth-input-wrap">
                  <UserRound size={17} aria-hidden="true" />
                  <input
                    type="text"
                    name="name"
                    autoComplete="name"
                    placeholder="How should we call you?"
                    value={name}
                    onChange={event => setName(event.target.value)}
                    maxLength={80}
                    required
                  />
                </span>
              </label>
            )}

            <label className="auth-field">
              <span>Email address</span>
              <span className="auth-input-wrap">
                <Mail size={17} aria-hidden="true" />
                <input
                  type="email"
                  name="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={event => setEmail(event.target.value)}
                  maxLength={254}
                  required
                />
              </span>
            </label>

            <label className="auth-field">
              <span>Password</span>
              <span className="auth-input-wrap">
                <LockKeyhole size={17} aria-hidden="true" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  autoComplete={isRegistering ? 'new-password' : 'current-password'}
                  placeholder={isRegistering ? 'At least 8 characters' : 'Enter your password'}
                  value={password}
                  onChange={event => setPassword(event.target.value)}
                  minLength={isRegistering ? 8 : 1}
                  maxLength={128}
                  required
                />
                <button className="auth-password-toggle" type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword(value => !value)}>
                  {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                </button>
              </span>
            </label>

            {isRegistering && (
              <label className="auth-field">
                <span>Confirm password</span>
                <span className="auth-input-wrap">
                  <LockKeyhole size={17} aria-hidden="true" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="confirm-password"
                    autoComplete="new-password"
                    placeholder="Enter your password again"
                    value={confirmPassword}
                    onChange={event => setConfirmPassword(event.target.value)}
                    maxLength={128}
                    required
                  />
                </span>
              </label>
            )}

            {error && <p className="auth-error" role="alert">{error}</p>}

            <button className="auth-submit" type="submit" disabled={isSubmitting}>
              <span>{isSubmitting ? 'Please wait...' : isRegistering ? 'Create my account' : 'Sign in'}</span>
              {!isSubmitting && <ArrowRight size={18} />}
            </button>
          </form>

          <p className="auth-switch-prompt">
            {isRegistering ? 'Already have an account?' : 'New to Smart Wardrobe?'}{' '}
            <button type="button" onClick={() => switchMode(isRegistering ? 'login' : 'register')}>
              {isRegistering ? 'Sign in' : 'Create an account'}
            </button>
          </p>
          <p className="auth-security-note"><LockKeyhole size={13} /> Your password is securely hashed and never stored as plain text.</p>
        </div>
      </section>
    </main>
  );
}
