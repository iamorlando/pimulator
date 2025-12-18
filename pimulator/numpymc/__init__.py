import os
from multiprocessing import Pool
import argparse
import time
import numpy as np


def worker(args):
    n, seed, chunk = args
    rng = np.random.default_rng(seed)
    inside = 0

    while n > 0:
        m = min(chunk, n)
        x = rng.random(m)
        y = rng.random(m)

        # in-place to reduce temporaries / peak memory
        np.square(x, out=x)
        np.square(y, out=y)
        x += y
        inside += int((x <= 1.0).sum())

        n -= m

    return inside


def simulate_pi(
    iters: int, n_procs: int | None = None, seed: int = 0, chunk: int = 5_000_000
) -> float:
    n_procs = n_procs or (os.cpu_count() or 1)
    n_procs = min(n_procs, iters)  # don’t spawn more procs than work
    print(f"Using {n_procs} processes")

    base, rem = divmod(iters, n_procs)
    jobs = [(base + (1 if i < rem else 0), seed + i, chunk) for i in range(n_procs)]

    with Pool(processes=n_procs) as pool:
        inside = sum(pool.map(worker, jobs))

    return 4.0 * inside / iters


def run_simulation(iterations: int, n_procs: int | None = None):

    t0 = time.time()
    pi = simulate_pi(iterations, n_procs=n_procs, seed=123)
    t1 = time.time()
    print(f"Estimated pi: {pi}")
    print(f"Time: {(t1 - t0) * 1000:.3f} miliseconds")
    return (pi, t1 - t0)


def _random_2d(
    n_points: int,
    seed: int = 0,
    chunk: int = 5_000_000,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    pts = np.empty((n_points, 2), dtype=float)

    idx = 0
    while idx < n_points:
        m = min(chunk, n_points - idx)
        pts[idx : idx + m, 0] = rng.random(m)
        pts[idx : idx + m, 1] = rng.random(m)
        idx += m

    return pts


def _quarter_inside_mask(pts01: np.ndarray) -> np.ndarray:
    x = pts01[:, 0]
    y = pts01[:, 1]
    return (x * x + y * y) <= 1.0


def _reflect_to_full_circle(pts01_inside: np.ndarray) -> np.ndarray:
    x = pts01_inside[:, 0]
    y = pts01_inside[:, 1]
    return np.vstack(
        [
            np.column_stack([x, y]),
            np.column_stack([-x, y]),
            np.column_stack([x, -y]),
            np.column_stack([-x, -y]),
        ]
    )


def run_mc_animation(
    iterations: int,
    interval_ms: int = 30,
    step: int = 50,
    seed: int = 123,
    chunk: int = 5_000_000,
):
    from matplotlib import rc
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation

    rc("animation", html="jshtml", embed_limit=500)

    t0 = time.time()
    n_points = iterations

    pts = _random_2d(n_points=n_points, seed=seed, chunk=chunk)
    mask = _quarter_inside_mask(pts)
    cum_inside = np.cumsum(mask)

    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    scat = ax.scatter([], [], s=3, alpha=0.8)

    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_aspect("equal", "box")
    ax.set_xticks([])
    ax.set_yticks([])

    circle = plt.Circle((0.0, 0.0), 1.0, fill=False, linewidth=2)
    ax.add_patch(circle)

    text = ax.text(
        0.02,
        0.98,
        "",
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        family="monospace",
    )

    def init():
        scat.set_offsets(np.empty((0, 2)))
        text.set_text("")
        return scat, text

    def update(frame):
        end = min((frame + 1) * step, n_points)
        inside_count = int(cum_inside[end - 1]) if end > 0 else 0

        pi_hat = 4.0 * inside_count / end if end > 0 else np.nan
        p_hat = inside_count / end if end > 0 else np.nan
        se = 4.0 * np.sqrt(p_hat * (1.0 - p_hat) / end) if end > 0 else np.nan
        ci_lo = pi_hat - 1.96 * se if end > 0 else np.nan
        ci_hi = pi_hat + 1.96 * se if end > 0 else np.nan

        inside_pts = pts[:end][mask[:end]]
        full_pts = (
            _reflect_to_full_circle(inside_pts) if inside_pts.size else np.empty((0, 2))
        )
        scat.set_offsets(full_pts)

        ax.set_title(
            f"Monte Carlo filling the unit circle (Pi={pi_hat:.4f} quarter-points)"
        )

        # text.set_text(
        #     f"pi_hat   = {pi_hat:.8f}\n"
        #     f"inside/N = {inside_count}/{end}\n\n"
        #     f"SE       = {se:.8f}\n"
        #     f"95% CI   = [{ci_lo:.8f}, {ci_hi:.8f}]"
        # )
        return scat, text

    n_frames = (n_points + step - 1) // step
    anim = FuncAnimation(
        fig,
        update,
        init_func=init,
        frames=n_frames,
        interval=interval_ms,
        blit=True,
        repeat=True,
    )

    pi_hat_final = 4.0 * cum_inside[-1] / n_points
    t1 = time.time()
    # print(f"Estimated pi: {pi_hat_final}")
    # print(f"Time: {(t1 - t0) * 1000:.3f} miliseconds")
    p_hat_final = pi_hat_final / 4.0
    se_final = 4.0 * np.sqrt(p_hat_final * (1.0 - p_hat_final) / n_points)
    ci_lo_final = pi_hat_final - 1.96 * se_final
    ci_hi_final = pi_hat_final + 1.96 * se_final
    # print(
    #     "MC pi_hat (N={:,}): {:.10f}   SE={:.10f}   95%=[{:.10f},{:.10f}]".format(
    #         n_points, pi_hat_final, se_final, ci_lo_final, ci_hi_final
    #     )
    # )
    plt.close(fig)
    plt.close(fig)
    try:
        from IPython.display import HTML
    except ImportError:
        return anim

    return HTML(anim.to_jshtml(default_mode="loop"))
