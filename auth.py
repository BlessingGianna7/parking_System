import numpy as np
import hashlib
import time

# =============================================================
# DOUBLE PENDULUM SIMULATION (RK4 method)
# Based on Lagrangian mechanics — same math as travisdoesmath.github.io
# RK4 is more accurate than simple Euler integration,
# which means more realistic chaos = better entropy
# =============================================================

def pendulum_derivatives(state, n=2, g=9.8):
    """
    Given current state [theta1, theta2, ..., omega1, omega2, ...],
    return derivatives [omega1, omega2, ..., alpha1, alpha2, ...]
    using the Lagrangian matrix equation Ax = b.
    """
    thetas = state[:n]
    omegas = state[n:]

    # Build A matrix: A[i][j] = (n - max(i,j)) * cos(theta_i - theta_j)
    A = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            A[i][j] = (n - max(i, j)) * np.cos(thetas[i] - thetas[j])

    # Build b vector
    b = np.zeros(n)
    for i in range(n):
        b_i = 0
        for j in range(n):
            b_i -= (n - max(i, j)) * np.sin(thetas[i] - thetas[j]) * omegas[j] ** 2
        b_i -= g * (n - i) * np.sin(thetas[i])
        b[i] = b_i

    # Solve for angular accelerations: A * alphas = b
    alphas = np.linalg.solve(A, b)

    return np.concatenate([omegas, alphas])


def rk4_step(state, dt, n=2, g=9.8):
    """One RK4 step forward in time."""
    k1 = pendulum_derivatives(state, n, g)
    k2 = pendulum_derivatives(state + 0.5 * dt * k1, n, g)
    k3 = pendulum_derivatives(state + 0.5 * dt * k2, n, g)
    k4 = pendulum_derivatives(state + dt * k3, n, g)
    return state + (dt / 6) * (k1 + 2*k2 + 2*k3 + k4)


def simulate_pendulum(steps=1000, dt=0.01, n=2):
    """
    Simulate n-tuple pendulum for `steps` steps using RK4.
    Start from random initial angles — tiny differences = wildly different outputs.
    Hash the final angles into a 16-char challenge code.
    """
    # Random initial conditions — this is the entropy source
    thetas = np.random.uniform(0, 2 * np.pi, n)
    omegas = np.zeros(n)
    state = np.concatenate([thetas, omegas])

    for _ in range(steps):
        state = rk4_step(state, dt, n)

    # Sample final angles and hash into challenge code
    final_thetas = state[:n]
    raw = "".join(f"{theta:.10f}" for theta in final_thetas)
    challenge = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return challenge


# =============================================================
# REGISTERED VEHICLES DATABASE
# In production: replace with a real DB (PostgreSQL like your RTB work)
# card_secret is stored on the physical RFID card — never transmitted raw
# =============================================================

REGISTERED_VEHICLES = {
    "RAH972U": {"card_secret": "alice_secret_key", "owner": "Alice"},
    "RAW972U": {"card_secret": "bob_secret_key",   "owner": "Bob"},
}

def get_card_secret(plate: str):
    vehicle = REGISTERED_VEHICLES.get(plate)
    return vehicle["card_secret"] if vehicle else None

def is_registered(plate: str) -> bool:
    return plate in REGISTERED_VEHICLES


# =============================================================
# CHALLENGE STORE — one challenge per plate, expires after 60 seconds
# =============================================================

pending_challenges = {}
CHALLENGE_TTL = 60  # seconds


def issue_challenge(plate: str) -> str:
    """Generate a pendulum-based one-time challenge for this plate."""
    challenge = simulate_pendulum()
    pending_challenges[plate] = {
        "challenge": challenge,
        "expires_at": time.time() + CHALLENGE_TTL
    }
    print(f"[AUTH] Challenge issued for {plate}: {challenge}")
    return challenge


def card_response(challenge: str, card_secret: str) -> str:
    """
    Compute what the RFID card should respond with.
    In production: this runs on the card's chip, not your server.
    The server never sees the secret — only this derived response.
    """
    combined = challenge + card_secret
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def verify_response(plate: str, rfid_response: str) -> bool:
    """
    Verify the RFID card's response against the pending challenge.
    Challenge is consumed immediately after one use (nonce behavior).
    """
    if plate not in pending_challenges:
        print(f"[AUTH] No pending challenge for {plate}. Rejected.")
        return False

    record = pending_challenges[plate]

    # Check expiry
    if time.time() > record["expires_at"]:
        print(f"[AUTH] Challenge expired for {plate}. Rejected.")
        del pending_challenges[plate]
        return False

    challenge = record["challenge"]
    del pending_challenges[plate]  # consumed — one time use only

    secret = get_card_secret(plate)
    if secret is None:
        print(f"[AUTH] Plate {plate} not in system. Rejected.")
        return False

    expected = card_response(challenge, secret)

    if rfid_response == expected:
        print(f"[AUTH] Verification passed for {plate}.")
        return True
    else:
        print(f"[AUTH] Wrong response for {plate}. Possible spoofing attempt.")
        return False


# =============================================================
# TEST — run this file directly to see it working
# python auth.py
# =============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("TEST 1: Legitimate user")
    print("=" * 50)
    plate = "RAH972U"
    secret = get_card_secret(plate)

    challenge = issue_challenge(plate)
    response = card_response(challenge, secret)      # card computes this
    print(f"Card response: {response}")
    result = verify_response(plate, response)
    print(f"Access granted: {result}")

    print()
    print("=" * 50)
    print("TEST 2: Attacker replays a stolen old response")
    print("=" * 50)
    challenge2 = issue_challenge(plate)
    print(f"Attacker uses old response: {response}")
    result2 = verify_response(plate, response)       # old response, new challenge
    print(f"Access granted: {result2}")

    print()
    print("=" * 50)
    print("TEST 3: Unregistered plate")
    print("=" * 50)
    fake_challenge = issue_challenge("RAX000X") if is_registered("RAX000X") else "skipped"
    print(f"Plate RAX000X registered: {is_registered('RAX000X')}")

    print()
    print("=" * 50)
    print("TEST 4: Two challenges are never the same")
    print("=" * 50)
    c1 = simulate_pendulum()
    c2 = simulate_pendulum()
    print(f"Challenge 1: {c1}")
    print(f"Challenge 2: {c2}")
    print(f"Same: {c1 == c2}")