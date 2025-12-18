use rand::Rng;
use rand::SeedableRng;
use rand::rngs::SmallRng;
use std::thread;

pub fn simulate_threads(iters: u64, num_threads: Option<u64>) -> (f64, u64, u128) {
    let timer = std::time::Instant::now();
    let n_threads = num_threads
        .unwrap_or(rayon::current_num_threads() as u64)
        .max(1);

    // let n_threads = 2;
    let base = iters / n_threads as u64;
    let rem = iters % n_threads as u64;

    let handles: Vec<_> = (0..n_threads)
        .map(|i| {
            thread::spawn(move || {
                let mut rng = SmallRng::seed_from_u64(0xC0FFEE_u64 ^ i);
                let n = base + if i < rem { 1 } else { 0 };

                let mut inside: u64 = 0;
                for _ in 0..n {
                    let x: f64 = rng.random();
                    let y: f64 = rng.random();
                    if x * x + y * y <= 1.0 {
                        inside += 1;
                    }
                }
                inside
            })
        })
        .collect();

    let inside: u64 = handles.into_iter().map(|h| h.join().unwrap()).sum();
    (
        4.0 * (inside as f64) / (iters as f64),
        n_threads,
        timer.elapsed().as_millis(),
    )
}
