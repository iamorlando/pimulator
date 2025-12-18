from pimulator.rust import simulate_threads as run_rust_simulation


def run_simulation(iterations: int, n_threads: int | None = None):
    pi, threads, milis = run_rust_simulation(iterations, num_threads=n_threads)
    print(f"Estimated pi: {pi}")
    print(f"Time: {milis:.3f} miliseconds")
    return (pi, threads, milis)


__all__ = ["run_simulation"]
