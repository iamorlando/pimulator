# Write and Call Rust from Python
Sometimes Python just won't cut it. Suppose you need to run a simulation for example, in Python you are limited to a single thread, plus the interpreter carries overhead that becomes noticeable when calling even very simple code thousands or millions of times.

In these situations NumPy or other high-performing computational libraries work well. They achieve their performance by delegating low level looping to C. But sometimes the APIs exposed by these libraries isn't enough to accommodate some per-path operation you might need to do. In situations like these you can write the inner loop easily with Rust and then include that functionality as part of your broader Python library. Doing this requires a small amount of configuration that, although simple, might not be easy to get right the first time.

Because I am a Python developer, Rust is usually something I layer onto my project, so that is how I will present this. Let's start with an existing Python project. The minimal pyproject.toml looks like this:

```toml
[project]
name = "pimulator"
version = "0.1.0"
requires-python = ">=3.14"
```

You can access the pimulator GitHub repo to see the fully built out example for a minimal Python/Rust mixed project. For now let's continue with our barebones, Python only, example. If you don't use `pyproject.toml`, you will need to add it to the root of your project.

## Maturin
Maturin is a Python module that builds your Rust code and binds it to your Python. It builds your Rust into a binary. If you plan on publishing your Python via wheels rather than sharing your source, then Maturin will bind the Rust binary into the wheel.

### Install Maturin in Your Python Environment
```bash
source .venv/bin/activate
pip install maturin
```

### Modify `pyproject.toml` to Build Using Maturin
Add this to `pyproject.toml`
```toml
[build-system]
requires = ["maturin>=1.10,<2.0"]
build-backend = "maturin"
```

### Configure Maturin
Finally we add this to `pyproject.toml`
```toml
[tool.maturin]
module-name = "pimulator.rust"
bindings = "pyo3"
```
`module-name` here refers to the name Python will see for the compiled Rust binaries. `pimulator.rust` means our import in Python will look like:
```python
from pimulator.rust import foo
```

### Setting Up the Rust Library
I will assume you have installed Rust. If not then you will want to have Cargo installed, as well as be able to compile Rust code.

Back to our library, create a directory where you will keep your Rust code. I usually call this, `rust`.
```bash
mkdir rust
cd rust
```
Now create your Rust lib file inside a directory called src:
```bash
mkdir src
touch src/lib.rs
```
Place this code example:
```rust
// rust/src/lib.rs
use pyo3::prelude::*;

#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

/// This must be named `rust` to match `module-name = "pimulator.rust"`.
#[pymodule]
fn rust(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    Ok(())
}

```

In the Git repo for this tutorial you will find I have created multiple modules that are visible to Python, but this code will serve for our minimal example.

#### Cargo
To finish setting up Rust in our once pure-Python project we add Cargo.toml. This is essentially Rust's pyproject equivalent. It will list all the dependencies you install for your Rust library, and has some amazing features. For example, if you want to see docs for all your dependencies, you can run `cargo doc --open`. I like to place Cargo.toml at the root of my project even though the standard setup is to put it inside the `rust` directory. To place `Cargo.toml` in the root I need to add this to `pyproject.toml`.

```toml
[tool.maturin]
module-name = "pimulator.rust"
bindings = "pyo3"
manifest-path = "Cargo.toml" # <- add this
```

In the root of your project add `Cargo.toml`
```bash
touch Cargo.toml
```

Place this configuration in your `Cargo.toml`
```toml
[package]
name = "pimulator"
version = "0.1.0"
edition = "2024"

[lib]
name = "rust"
path = "rust/src/lib.rs"
crate-type = ["cdylib"]

[dependencies]
pyo3 = "0.27.0"
```
The above is the minimum required set of keys. The name `rust` refers to the main module you are exporting in your Rust library. The package name is set to pimulator. This means that Cargo will build your library and expose it as `pimulator.rust`, which matches what we said we wanted in `pyproject.toml` `[tool.maturin]`.

### Building the Binaries
To make coding in Rust seamless and comfortable, it would be nice if each time we change the Rust code we have that reflected in our Python. To do this we use cargo watch. I personally don't like writing this command each time I start coding, so I use a MakeFile, it looks like this:

```make
VENV := .venv
PY   := $(VENV)/bin/python
watch:
	cargo install cargo-watch && cargo watch -C . -w rust/src -w Cargo.toml --ignore target -s "$(PY) -m maturin develop"
release:
	$(PY) -m maturin build --release --out ./dist
```
With this MakeFile you would watch the `rust` folder with
```bash
make watch
```
Now every time you save a Rust file the binary will be quickly rebuilt and your testing will pick up your latest Rust code.

If you want to publish your code you can use the wheel created with
```bash
make release
```
Make sure you build the right wheel for the right target. Maturin automatically generates an architecture/target matrix which you can copy paste into a GitHub Actions workflow. You can generate it with:
```bash
maturin generate-ci github
```
That's it! To conclude, these are the files you will have ended up with:

## Files You Should Have

### `pyproject.toml`
```toml
[project]
name = "pimulator"
version = "0.1.0"
description = ""
requires-python = ">=3.14"


[build-system]
requires = ["maturin>=1.10,<2.0"]
build-backend = "maturin"

[tool.maturin]
bindings = "pyo3"
module-name = "pimulator.rust"
manifest-path = "Cargo.toml"

```

### `Cargo.toml`
```toml
[package]
name = "pimulator"
version = "0.1.0"
edition = "2024"

[lib]
name = "rust"
path = "rust/src/lib.rs"
crate-type = ["cdylib"]

[dependencies]
pyo3 = "0.27.0"

```

### `rust/src/lib.rs`
```rust
use pyo3::prelude::*;

#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

/// This must be named `rust` to match `module-name = "pimulator.rust"`.
#[pymodule]
fn rust(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    Ok(())
}
```

### `pimulator/__init__.py`
```python
from pimulator.rust import sum_as_string
```

### `MakeFile`
```make
VENV := .venv
PY   := $(VENV)/bin/python
watch:
	cargo install cargo-watch && cargo watch -C . -w rust/src -w Cargo.toml --ignore target -s "$(PY) -m maturin develop"
release:
	$(PY) -m maturin build --release --out ./dist
```

And that's all there is to it! You've now wired up Rust functions to your Python library. Test it in a notebook or in the terminal with
```bash
python -c "from pimulator import sum_as_string;print(sum_as_string(1,2))"
```
