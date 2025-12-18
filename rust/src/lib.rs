// rust/src/lib.rs

mod montecarlo;
use pyo3::prelude::*;

#[pyfunction]
#[pyo3(signature = (iters, num_threads=None))]
fn simulate_threads(iters: u64, num_threads: Option<u64>) -> (f64, u64, u128) {
    montecarlo::simulate_threads(iters, num_threads)
}

#[pymodule]
fn rust(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(simulate_threads, m)?)?;
    Ok(())
}
